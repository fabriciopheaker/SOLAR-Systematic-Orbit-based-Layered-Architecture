# SOLAR-ARCH-024 — SQL montado por interpolação.
#
# O `unsafe_sql_scanner` só produz `UnsafeSql` quando há VALOR
# DINÂMICO entrando na string; concatenar pedaços literais não é
# perigoso e não chega aqui.
#
# ⚠️ LIMITE CONHECIDO: o filtro é pelo segmento `persistence` do
# módulo. SQL inseguro em qualquer outra camada NÃO é flagrado.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule
from nucleus.rules.scanner.unsafe_sql import UnsafeSql


class PersistenceMustNotBuildUnsafeSql(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-024

    Persistência NÃO pode construir SQL inseguro.

    É VIOLAÇÃO:

        "SELECT * FROM users WHERE id = " + user_id
        f"SELECT * FROM users WHERE id = {user_id}"
        "SELECT * FROM users WHERE id = %s" % user_id
        "SELECT * FROM users WHERE id = {}".format(user_id)

    Correto — SQL estático com parâmetros:

        "SELECT * FROM users WHERE id = :id"
        cursor.execute(sql, {"id": user_id})

    O contexto desta regra é um UnsafeSql.

    ESCOPO: a regra fiscaliza a camada de Persistência
    (`*.persistence`), que é a responsável por falar com o banco.
    """

    # Segmento que identifica a camada de Persistência.
    PERSISTENCE_SEGMENT = "persistence"

    def code(self) -> str:
        return "SOLAR-ARCH-024"

    def description(self) -> str:
        return "Persistência não pode construir SQL inseguro."

    def validate(self, unsafe: UnsafeSql) -> None:

        # O contexto `UnsafeSql` cobre o projeto inteiro; esta regra
        # fiscaliza só a camada de Persistência, que é quem fala com
        # o banco. Interpolação em outro lugar é problema de outra
        # camada.
        if not self._is_persistence(unsafe):
            return

        raise SolarException(
            self._build_message(unsafe)
        )

    def _is_persistence(self, unsafe: UnsafeSql) -> bool:

        # `in unsafe.module.split(".")` e não `"persistence" in
        # unsafe.module`: o teste é sobre o SEGMENTO do módulo. Com
        # substring, um módulo chamado `persistence_helpers` ou
        # `user_persistence` casaria sem ser a camada.
        return (
            self.PERSISTENCE_SEGMENT
            in unsafe.module.split(".")
        )

    def _build_message(self, unsafe: UnsafeSql) -> str:

        return (
            f"{self.code()}: "
            f"SQL construído por {unsafe.kind} em "
            f"{unsafe.file}:{unsafe.line}. "
            f"SQL deve ser ESTÁTICO e parametrizado "
            f"(ex.: '... WHERE id = :id' + parâmetros), "
            f"nunca interpolado com valores."
        )
