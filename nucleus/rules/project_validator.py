# Ponto de execução das regras arquiteturais sobre o projeto.
#
# Amarra as três peças que existiam soltas: o SCANNER (descreve o
# fato), a RULE (decide a política) e o RELATÓRIO (mostra o
# resultado). Sem este módulo, scanners e regras só rodavam
# dentro dos testes.
from dataclasses import dataclass
from pathlib import Path

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.authentication_must_not_be_scattered_in_controllers import (  # noqa: E501
    AuthenticationMustNotBeScatteredInControllers
)
from nucleus.rules.architecture.controller_must_not_implement_authentication import (  # noqa: E501
    ControllerMustNotImplementAuthentication
)
from nucleus.rules.architecture.controller_must_return_resource import (
    ControllerMustReturnResource
)
from nucleus.rules.architecture.errors_must_not_leak_internals import (
    ErrorsMustNotLeakInternals
)
from nucleus.rules.architecture.external_communication_belongs_to_satellites import (  # noqa: E501
    ExternalCommunicationBelongsToSatellites
)
from nucleus.rules.architecture.http_input_must_pass_through_sanitization_and_validation import (  # noqa: E501
    HttpInputMustPassThroughSanitizationAndValidation
)
from nucleus.rules.architecture.models_cannot_depend_on_persistence import (
    ModelsCannotDependOnPersistence
)
from nucleus.rules.architecture.models_must_access_orm_through_database import (
    ModelsMustAccessOrmThroughDatabase
)
from nucleus.rules.architecture.models_must_live_in_their_own_file import (
    ModelsMustLiveInTheirOwnFile
)
from nucleus.rules.architecture.orbits_must_use_database_facade import (
    OrbitsMustUseDatabaseFacade
)
from nucleus.rules.architecture.orm_belongs_to_driver import (
    OrmBelongsToDriver
)
from nucleus.rules.architecture.outbound_requests_must_not_use_untrusted_url import (  # noqa: E501
    OutboundRequestsMustNotUseUntrustedUrl
)
from nucleus.rules.architecture.persistence_belongs_to_orbits_database import (  # noqa: E501
    PersistenceBelongsToOrbitsDatabase
)
from nucleus.rules.architecture.persistence_must_not_build_unsafe_sql import (
    PersistenceMustNotBuildUnsafeSql
)
from nucleus.rules.architecture.planet_cannot_depend_on_driver import (
    PlanetCannotDependOnDriver
)
from nucleus.rules.architecture.planet_cannot_depend_on_planet import (
    PlanetCannotDependOnPlanet
)
from nucleus.rules.architecture.planet_cannot_know_nucleus_infrastructure import (  # noqa: E501
    PlanetCannotKnowNucleusInfrastructure
)
from nucleus.rules.architecture.planet_must_have_standard_structure import (
    PlanetMustHaveStandardStructure
)
from nucleus.rules.architecture.repository_cannot_depend_on_database import (
    RepositoryCannotDependOnDatabase
)
from nucleus.rules.architecture.repository_must_use_persistence import (
    RepositoryMustUsePersistence
)
from nucleus.rules.architecture.request_data_must_not_become_entities_directly import (  # noqa: E501
    RequestDataMustNotBecomeEntitiesDirectly
)
from nucleus.rules.architecture.resources_must_not_expose_secrets import (
    ResourcesMustNotExposeSecrets
)
from nucleus.rules.architecture.routes_must_be_declared_explicitly import (
    RoutesMustBeDeclaredExplicitly
)
from nucleus.rules.architecture.routes_must_live_in_route_modules import (
    RoutesMustLiveInRouteModules
)
from nucleus.rules.architecture.routes_must_point_to_controller import (
    RoutesMustPointToController
)
from nucleus.rules.architecture.secrets_must_not_appear_in_source import (
    SecretsMustNotAppearInSource
)
from nucleus.rules.architecture.secrets_must_not_be_hardcoded import (
    SecretsMustNotBeHardcoded
)
from nucleus.rules.architecture.tokens_must_be_secure import (
    TokensMustBeSecure
)
from nucleus.rules.architecture.uploads_must_use_storage import (
    UploadsMustUseStorage
)
from nucleus.rules.report import (
    CheckResult,
    ProjectReport,
    Violation,
)
from nucleus.rules.rule import Rule
from nucleus.rules.scanner.architecture_scanner import ArchitectureScanner
from nucleus.rules.scanner.controller_auth_check_scanner import (
    ControllerAuthCheckScanner
)
from nucleus.rules.scanner.controller_return_scanner import (
    ControllerReturnScanner
)
from nucleus.rules.scanner.controller_security_scanner import (
    ControllerSecurityScanner
)
from nucleus.rules.scanner.error_exposure_scanner import (
    ErrorExposureScanner
)
from nucleus.rules.scanner.http_input_scanner import HttpInputScanner
from nucleus.rules.scanner.mass_assignment_scanner import (
    MassAssignmentScanner
)
from nucleus.rules.scanner.module_classes_scanner import (
    ModuleClassesScanner
)
from nucleus.rules.scanner.outbound_request_scanner import (
    OutboundRequestScanner
)
from nucleus.rules.scanner.planet_scanner import PlanetScanner
from nucleus.rules.scanner.resource_exposure_scanner import (
    ResourceExposureScanner
)
from nucleus.rules.scanner.route_scanner import RouteScanner
from nucleus.rules.scanner.secret_content_scanner import (
    SecretContentScanner
)
from nucleus.rules.scanner.secret_scanner import SecretScanner
from nucleus.rules.scanner.token_security_scanner import (
    TokenSecurityScanner
)
from nucleus.rules.scanner.unsafe_sql_scanner import UnsafeSqlScanner
from nucleus.rules.scanner.upload_handling_scanner import (
    UploadHandlingScanner
)


@dataclass(frozen=True)
class Check:
    """
    Uma verificação: um SCANNER e as regras que falam do contexto
    que ele produz.

    O agrupamento não é decorativo — cada contexto tem o seu
    RuleEngine, e passar um alvo de um contexto para um
    RuleEngine de outro quebra a execução.

    name:
        Nome do contexto (ex.: "Dependency").

    scanner:
        Classe do scanner; recebe a raiz do projeto.

    rules:
        Regras que entendem do contexto desse scanner.
    """

    # Nome do contexto; é ele que aparece no relatório e no
    # `check` da linha de comando.
    name: str

    # A CLASSE do scanner, não a instância: cada check recebe a
    # raiz do projeto no momento de varrer, e a mesma classe serve
    # a varreduras diferentes.
    scanner: type

    # Regras que sabem ler o contexto produzido por esse scanner.
    # Passar um alvo de outro contexto para estas regras quebra a
    # execução — o RuleEngine é por contexto.
    rules: tuple[Rule, ...]


def project_checks() -> tuple[Check, ...]:
    """
    Registro das verificações que rodam sobre o projeto.

    A ORDEM é a de execução, e o relatório sai nesta ordem.

    Fora daqui, de propósito:

        SOLAR-ARCH-004   absorvida pela SOLAR-ARCH-001;
        SOLAR-ARCH-015   o contexto é o contrato nomeado do UseCase,
                         e ainda não há scanner para ele.
    """

    # A ORDEM das tuplas abaixo é a ordem de execução e a ordem
    # do relatório. O agrupamento segue a REGRA, não a pasta:
    # cada scanner é dono do seu contexto.
    return (
        # Um scanner para o projeto inteiro (dependências entre
        # módulos) e onze regras que leem esse mesmo contexto.
        Check("Dependency", ArchitectureScanner, (
            PlanetCannotDependOnPlanet(),
            RepositoryCannotDependOnDatabase(),
            RepositoryMustUsePersistence(),
            ModelsCannotDependOnPersistence(),
            ModelsMustAccessOrmThroughDatabase(),
            PersistenceBelongsToOrbitsDatabase(),
            OrbitsMustUseDatabaseFacade(),
            PlanetCannotDependOnDriver(),
            OrmBelongsToDriver(),
            PlanetCannotKnowNucleusInfrastructure(),
            ExternalCommunicationBelongsToSatellites(),
        )),
        Check("HttpInput", HttpInputScanner, (
            HttpInputMustPassThroughSanitizationAndValidation(),
        )),
        Check("RouteDeclaration", RouteScanner, (
            RoutesMustBeDeclaredExplicitly(),
            RoutesMustPointToController(),
            RoutesMustLiveInRouteModules(),
        )),
        Check("PlanetStructure", PlanetScanner, (
            PlanetMustHaveStandardStructure(),
        )),
        Check("SecretLiteral", SecretScanner, (
            SecretsMustNotBeHardcoded(),
        )),
        Check("ResourceExposure", ResourceExposureScanner, (
            ResourcesMustNotExposeSecrets(),
        )),
        Check("ControllerSecurityUsage", ControllerSecurityScanner, (
            ControllerMustNotImplementAuthentication(),
        )),
        Check("ControllerReturn", ControllerReturnScanner, (
            ControllerMustReturnResource(),
        )),
        Check("SecretOccurrence", SecretContentScanner, (
            SecretsMustNotAppearInSource(),
        )),
        Check("UnsafeSql", UnsafeSqlScanner, (
            PersistenceMustNotBuildUnsafeSql(),
        )),
        Check("UploadHandling", UploadHandlingScanner, (
            UploadsMustUseStorage(),
        )),
        Check("ControllerAuthChecks", ControllerAuthCheckScanner, (
            AuthenticationMustNotBeScatteredInControllers(),
        )),
        Check("TokenUsage", TokenSecurityScanner, (
            TokensMustBeSecure(),
        )),
        Check("ErrorExposure", ErrorExposureScanner, (
            ErrorsMustNotLeakInternals(),
        )),
        Check("EntityBinding", MassAssignmentScanner, (
            RequestDataMustNotBecomeEntitiesDirectly(),
        )),
        Check("OutboundRequest", OutboundRequestScanner, (
            OutboundRequestsMustNotUseUntrustedUrl(),
        )),
        Check("ModuleClasses", ModuleClassesScanner, (
            ModelsMustLiveInTheirOwnFile(),
        )),
    )


class ProjectValidator:
    """
    Executa TODAS as regras arquiteturais sobre o projeto.

    É o ponto de execução que faltava: os scanners e as regras
    existiam, mas nada os invocava fora dos testes.

        report = ProjectValidator(Path(".")).validate()

        if not report.is_clean():
            print(report)

    Diferença em relação ao RuleEngine: o RuleEngine PARA na
    primeira violação (o contrato é "validar ou levantar"). Aqui a
    intenção é o contrário — mostrar TUDO o que está fora do lugar
    de uma vez, para não transformar a correção em um jogo de
    descobre-e-corrige. Por isso cada regra é chamada
    individualmente e a exceção é recolhida como violação.

    Um erro que NÃO seja SolarException não é recolhido: seria bug
    na regra ou no scanner, e deve aparecer como erro.
    """

    def __init__(self, root: Path, checks=None):
        # `resolve()` e não `Path(root)`: o scanner subtrai a raiz
        # do caminho de cada arquivo para gravar o local RELATIVO
        # no relatório. Sem o caminho absoluto normalizado, essa
        # subtração falha quando o `check` roda de outro diretório.
        self.root = Path(root).resolve()

        # `checks` injetável: os testes passam um check só para
        # exercitar uma regra sem varrer o projeto todo.
        self.checks = (
            project_checks()
            if checks is None
            else tuple(checks)
        )

    def validate(self) -> ProjectReport:
        """
        Varre o projeto e devolve o relatório.
        """

        results: list[CheckResult] = []
        rules = 0

        for check in self.checks:

            # Conta antes de rodar: a contagem é do que FOI
            # aplicado, e um check que levante por bug do scanner
            # já teria aplicado as suas regras.
            rules += len(check.rules)

            # Um resultado por check, na ordem declarada em
            # `project_checks()`.
            results.append(
                CheckResult(
                    name=check.name,
                    violations=tuple(self._check(check))
                )
            )

        return ProjectReport(
            results=tuple(results),
            rules=rules
        )

    def _check(self, check: Check) -> list[Violation]:
        """
        Roda as regras de um check sobre cada alvo do seu scanner.
        """

        violations: list[Violation] = []

        # O scanner lê o projeto inteiro uma vez e devolve TODOS
        # os alvos do contexto; as regras do check rodam sobre
        # cada um deles.
        for target in check.scanner(self.root).scan():

            violations.extend(
                self._apply(check, target)
            )

        return violations

    def _apply(
        self,
        check: Check,
        target
    ) -> list[Violation]:
        """
        Aplica as regras do check a um alvo.
        """

        violations: list[Violation] = []

        for rule in check.rules:

            # `try` por regra, e não em volta do laço: uma
            # violação não pode impedir as regras seguintes de
            # falarem. O objetivo aqui é listar TUDO o que está
            # fora do lugar de uma vez.
            try:
                rule.validate(target)

            # Só `SolarException` é recolhida — ela significa
            # "o projeto viola a regra". Qualquer outro erro é bug
            # na regra ou no scanner e DEVE subir como erro:
            # engolir aqui esconderia defeito do próprio
            # validador.
            except SolarException as error:

                violations.append(
                    Violation(
                        rule=rule.code(),
                        description=rule.description(),
                        message=str(error),
                        location=_location(target)
                    )
                )

        return violations


def _location(target) -> str:
    """
    Local do alvo, quando o contexto informa.

    Os contextos carregam o local de formas diferentes
    (`file`/`line`, `path`, `name`), e alguns não carregam nada —
    a mensagem da regra continua dizendo onde é.
    """

    # `getattr` com padrão: os contextos são dataclasses
    # diferentes e nem todos carregam local. Perguntar o que
    # existe é mais barato que obrigar todo contexto a ter os
    # mesmos campos.
    file = getattr(target, "file", None)
    line = getattr(target, "line", None)

    # Linha junto do arquivo quando houver: "arquivo:linha" é o
    # formato que o terminal e o editor entendem como clique.
    if file and line is not None:
        return f"{file}:{line}"

    if file:
        return str(file)

    # Ordem de preferência: `path` é o local real; `name` é o
    # último recurso (ex.: contextos de estrutura, que só têm o
    # nome do Planet).
    for attribute in ("path", "name"):

        value = getattr(target, attribute, None)

        if value:
            return str(value)

    return ""
