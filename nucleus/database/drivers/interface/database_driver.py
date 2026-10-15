"""
Contrato do driver de persistência.

A fachada `Database` fala com qualquer driver que implemente
isto. É o que permite trocar SQLAlchemy por outra tecnologia sem
tocar na aplicação (SOLAR-ARCH-010).
"""

from abc import ABC, abstractmethod


class DatabaseDriver(ABC):
    """
    Contrato de acesso ao banco da SOLAR.

    É o que permite trocar a tecnologia de persistência sem tocar na
    aplicação (SOLAR-ARCH-010): a fachada `Database` fala só com
    este contrato, e o driver concreto é escolhido na montagem.
    """

    # Ciclo de vida separado do uso: a fachada conecta na montagem e
    # desconecta no shutdown, e entre esses dois pontos ninguém mais
    # precisa pensar em conexão.
    @abstractmethod
    def connect(self) -> None:
        """
          Estabelece a conexão com o banco de dados.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """
          Encerra a conexão com o banco de dados.
        """
        raise NotImplementedError

    # Existe para a aplicação poder dizer "estou no ar" sem tentar
    # uma consulta de verdade — e sem que a rota de health precise
    # conhecer o driver.
    @abstractmethod
    def health_check(self) -> bool:
        """
          Verifica se a conexão com o banco está funcional.
        """
        raise NotImplementedError

    # Os dois acessos abaixo não são uso: são o vocabulário que o
    # driver ENTREGA para os models (colunas, tipos, sessão). Sem
    # eles, um Model teria que importar sqlalchemy direto — que é
    # exatamente o que a SOLAR-ARCH-011 proíbe.
    @abstractmethod
    def orm(self):
      """
        Retorna a infraestrutura ORM utilizada pelo driver.

        Cada driver deve disponibilizar sua implementação
        de ORM através deste método.
      """
      raise NotImplementedError

    @abstractmethod
    def model(self):
      """
        Retorna a infraestrutura de modelagem utilizada pelo driver.

        Cada driver deve disponibilizar sua implementação de
        modelagem (colunas, tipos, etc.) através deste método.
      """
      raise NotImplementedError

    # A sessão entra no CONTRATO porque é por ela que a Persistence
    # lê e grava. Sem ela aqui, quem quisesse gravar teria que
    # alcançar o driver por fora — e trocar de tecnologia deixaria
    # de ser possível.
    @abstractmethod
    def session(self):
        """
        Sessão de trabalho da ORM.

        O driver a cria em `connect()` e a entrega aqui. É o único
        ponto de contato da Persistence com a tecnologia.
        """
        raise NotImplementedError

    @abstractmethod
    def sync(self, *, prune=True) -> None:
        """
        Sincroniza o ESQUEMA do banco com os Models conhecidos.

        Cria o que ainda não existe e ALTERA o que já existe e mudou.

        O driver não sabe QUAIS tabelas existem — ele sabe o que
        estiver registrado na base da ORM. Quem importa os Models
        antes de chamar isto é a fachada `Database`.

        `prune` remove o que sobrar no banco e não existir mais no
        Model. É `True` por padrão: esquema que só cresce acumula
        estrutura que ninguém mais declara.

        É o mínimo para a aplicação funcionar sem um mecanismo de
        migrations — sincronizar esquema não é versionar esquema. Com
        migrations (Alembic com revisões, ou equivalente), este passo
        sai daqui e vira etapa do deploy.
        """
        raise NotImplementedError