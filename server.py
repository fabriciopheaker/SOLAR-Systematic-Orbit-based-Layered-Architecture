from pathlib import Path

from nucleus.kernel import PROJECT_ROOT, Kernel
from nucleus.rules.project_validator import ProjectValidator
from nucleus.rules.report import ProjectReport
from observatory.log.error_log import ErrorLog
from observatory.solar import audit


class Server:
    """
    Sobe o servidor da aplicação.

    O Kernel MONTA; o Server SOBE.

        python server.py

    Aqui também é onde o Observatório se liga. Não é escolha de
    gosto: a direção da dependência é Observatory → Nucleus, então
    o Nucleus não pode conhecer o Observatório. Quem conhece os
    dois é este ponto, que está fora de ambos.

    E é aqui que a arquitetura é VERIFICADA a cada subida, pelo
    mesmo motivo: o Kernel não pode chamar o verificador (ele vive
    no Nucleus, o verificador no Observatório), e o Server está
    fora dos dois e pode.
    """

    def __init__(
        self,
        kernel=None,
        error_log_path=None,
        verification_root=None
    ):

        # O Kernel pode ser injetado. Nos testes entra um de
        # mentira, e assim a subida é conferida sem montar nada de
        # verdade nem conectar a banco nenhum.
        self.kernel = kernel or Kernel()

        # Onde o banco de erros do Observatório fica gravado.
        # None = o caminho padrão (observatory/data/solar.sqlite).
        # Os testes passam uma pasta temporária, para não escrever
        # no projeto.
        self.error_log_path = error_log_path

        # Que código a verificação arquitetural varre. O padrão é a
        # raiz do projeto — a MESMA que o Kernel usa, e não uma
        # segunda definição dela. Injetável para o teste apontar
        # para uma pasta própria em vez de varrer o projeto.
        self.verification_root = (
            Path(verification_root) if verification_root else PROJECT_ROOT
        )

        self.error_log = None

    # -----------------------------------------------------------------
    # Montagem e subida
    # -----------------------------------------------------------------

    def prepare(self):
        """
        Monta a aplicação e liga o Observatório.

        Devolve a aplicação pronta.

        Está separado de `run()` para que se possa MONTAR sem subir
        servidor — é o que os testes usam.
        """

        # MONTA — quem sabe montar é o Kernel; aqui só se pede.
        app = self.kernel.mount()

        # OBSERVA — abre o registro de erros do Observatório.
        #
        # O `solar_id` diz de QUAL aplicação é o erro e o
        # `environment` diz em que ambiente ele aconteceu. Os dois
        # vêm da montagem, e não de quem chamou a rota: quem chama
        # a rota não sabe (nem deveria saber) onde gravar.
        self.error_log = ErrorLog(
            path=self.error_log_path,
            solar_id=self.kernel.identity.solar_id,
            environment=self.kernel.config.get("APP_ENV"),
        )

        # Liga o registro ao tratamento de erro. A partir daqui,
        # todo erro que o ErrorHandler tratar chega neste banco —
        # sem que o Nucleus saiba que ele existe.
        self.kernel.observe(self.error_log)

        return app

    # -----------------------------------------------------------------
    # Verificação da arquitetura
    # -----------------------------------------------------------------

    def verify_architecture(self) -> ProjectReport:
        """
        Verifica a arquitetura e mostra o resultado.

        É o MESMO verificador do comando `check`; o que muda é a
        POLÍTICA de registro:

            `check`   registra SEMPRE — alguém pediu a verificação, e
                      o arquivo é a resposta;

            aqui      registra só quando há VIOLAÇÃO. Esta verificação
                      roda sozinha a cada subida: gravar um arquivo
                      idêntico de cada vez encheria o diretório de
                      auditoria e afogaria o registro que importa.

        Devolve o relatório, para quem chamou decidir o que fazer com
        ele.
        """

        # A varredura é CARA: são 16 verificações independentes, e cada
        # uma lê e analisa a árvore inteira do projeto. O aviso existe
        # para a espera não parecer travamento — e o `flush=True` existe
        # porque, sem ele, a linha ficaria no buffer e a espera
        # continuaria silenciosa.
        print("verificando a arquitetura...", flush=True)

        report = ProjectValidator(self.verification_root).validate()

        # A linha de status vem PRIMEIRO nos dois casos: é ela que a
        # subida mostra de relance, e é ela que um `grep` acha no log.
        print(f"arquitetura: {report.status()}")

        if report.is_clean():
            return report

        # Com violação, o relatório INTEIRO: é a hora de mostrar o que
        # está fora do lugar, com local e mensagem. Ele repete o
        # resultado no fim de propósito — o relatório também é lido
        # sozinho, dentro do arquivo de auditoria.
        print(report)

        saved = audit.record_violation(report, self.verification_root)

        if saved is not None:
            print(f"auditoria: {audit.display_path(saved)}")

        return report

    def run(self) -> None:
        """
        Verifica a arquitetura, monta e sobe.
        """

        # VERIFICA primeiro, e antes de montar: a verificação é sobre o
        # CÓDIGO e não depende de nada montado — e assim o resultado
        # aparece antes do banner do servidor, que é onde a atenção de
        # quem sobe está.
        self.verify_architecture()

        app = self.prepare()

        config = self.kernel.config

        try:
            app.run(
                # Endereço e porta vêm do ambiente: {APP_ENV}_HOST e
                # {APP_ENV}_PORT no arquivo .env. Quem decide onde a
                # aplicação escuta é o ambiente, não o código.
                host=config.get("HOST"),
                port=int(config.get("PORT")),

                # Debug só em DEV. Em TEST e PROD, desligado.
                debug=config.get("APP_ENV") == "DEV",

                # O recarregador fica DESLIGADO de propósito.
                #
                # Montar tem efeito colateral: grava a identidade
                # no arquivo de ambiente e abre o banco do
                # Observatório. Com o recarregador ligado, a
                # montagem roda duas vezes (o processo pai e o
                # filho), e as duas escrevem.
                use_reloader=False,
            )

        finally:
            # Subiu e parou, ou falhou ao subir: o que segura
            # recurso é encerrado de todo jeito.
            self.shutdown()

    def shutdown(self) -> None:
        """
        Encerra o que segura recurso.
        """

        # Fecha a conexão do banco da aplicação.
        self.kernel.shutdown()

        # Fecha o banco do Observatório. Quem abriu foi este
        # objeto, então é ele que fecha — e zera a referência para
        # que um segundo shutdown não feche duas vezes.
        if self.error_log is not None:

            self.error_log.close()
            self.error_log = None


def main() -> int:
    """
    Ponto de entrada da aplicação.
    """

    Server().run()

    # Só chega aqui quando o servidor para de forma limpa.
    return 0


if __name__ == "__main__":

    # Entrega o retorno de main() como código de saída do processo
    # — é o que a esteira e o sistema operacional leem.
    raise SystemExit(main())
