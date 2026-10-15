from nucleus.contracts.validator import Validator
from nucleus.exceptions.validation_exception import ValidationException
from nucleus.upload.file_sanitizer import upload_files
from nucleus.upload.file_signatures import matches, sniff
from nucleus.upload.upload_policy import UploadPolicy


class FileValidator(Validator):
    """
    Validator de UPLOAD.

    Valida as características ESTRUTURAIS da entrada:

        - arquivo foi enviado;
        - quantidade de arquivos;
        - arquivo vazio;
        - tamanho permitido;
        - extensão permitida;
        - MIME type permitido.

    Implementa o contrato Validator da SOLAR-ARCH-013, aplicando
    uma UploadPolicy.

    ESCOPO: regras de NEGÓCIO sobre o documento ("precisa ser um
    contrato válido com determinado número de contrato") NÃO
    pertencem aqui — ficam no UseCase/Domain.

    Acumula TODOS os problemas antes de lançar, para o cliente
    receber a lista completa.
    """

    def __init__(self, policy: UploadPolicy):
        self.policy = policy

    def validate(self, payload) -> None:
        """
        Valida os arquivos e lança ValidationException com todos
        os problemas encontrados.
        """

        files = upload_files(payload)

        # Acumula TUDO antes de levantar: quem está enviando recebe
        # a lista completa numa resposta só, em vez de descobrir um
        # problema por vez, a cada nova tentativa.
        errors = self._errors(files)

        if not errors:
            return

        # `code` estável, para o cliente tratar; a mensagem leva a
        # lista, para a pessoa ler.
        raise ValidationException(
            "Upload inválido: " + "; ".join(errors),
            code="INVALID_UPLOAD"
        )

    def _errors(self, files: list) -> list[str]:
        """
        Coleta os problemas da entrada.
        """

        # Sem arquivo nenhum não há o que inspecionar: é um erro
        # único, e não uma lista.
        if not files:
            return ["nenhum arquivo foi enviado"]

        errors: list[str] = []

        if len(files) > self.policy.max_files:
            errors.append(
                f"quantidade de arquivos acima do permitido "
                f"({len(files)} > {self.policy.max_files})"
            )

        for file in files:
            errors.extend(
                self._file_errors(file)
            )

        return errors

    def _file_errors(self, file) -> list[str]:
        """
        Coleta os problemas de um arquivo.
        """

        errors: list[str] = []

        # Arquivo vazio para AQUI. Sem conteúdo, tamanho e extensão
        # não dizem nada — e três erros para o mesmo problema só
        # confundiriam a mensagem.
        if not file.content:
            errors.append(f"'{file.name}' está vazio")
            return errors

        if not self.policy.allows_size(file.size):
            errors.append(
                f"'{file.name}' excede o tamanho permitido "
                f"({file.size} > {self.policy.max_size_bytes} bytes)"
            )

        if not self.policy.allows_extension(file.extension):
            errors.append(
                f"extensão '{file.extension}' não permitida para "
                f"'{file.name}'"
            )

        if not self.policy.allows_content_type(file.content_type):
            errors.append(
                f"tipo de conteúdo '{file.content_type}' não "
                f"permitido para '{file.name}'"
            )

        errors.extend(
            self._content_errors(file)
        )

        return errors

    def _content_errors(self, file) -> list[str]:
        """
        Confere se o CONTEÚDO corresponde ao tipo declarado.

        É o que impede um script renomeado para ".pdf" de entrar:
        a extensão e o MIME declarado podem mentir, as assinaturas
        (magic bytes) do arquivo não.
        """

        if not self.policy.verify_content:
            return []

        if matches(file.content, file.content_type):
            return []

        detected = sniff(file.content) or "não reconhecido"

        return [
            f"o conteúdo de '{file.name}' não corresponde ao tipo "
            f"declarado '{file.content_type}' "
            f"(detectado: '{detected}')"
        ]
