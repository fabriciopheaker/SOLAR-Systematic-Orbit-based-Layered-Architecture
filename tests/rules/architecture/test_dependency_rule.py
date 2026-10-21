import pytest

from nucleus.rules.scanner.dependency import Dependency
from nucleus.rules.architecture.planet_cannot_depend_on_planet import PlanetCannotDependOnPlanet
from nucleus.rules.architecture.repository_cannot_depend_on_database import RepositoryCannotDependOnDatabase
from nucleus.rules.architecture.repository_must_use_persistence import RepositoryMustUsePersistence

from nucleus.rules.architecture.models_cannot_depend_on_persistence import ModelsCannotDependOnPersistence

from nucleus.rules.architecture.models_must_access_orm_through_database import ModelsMustAccessOrmThroughDatabase

from nucleus.rules.architecture.persistence_belongs_to_orbits_database import PersistenceBelongsToOrbitsDatabase

from nucleus.rules.architecture.orbits_must_use_database_facade import OrbitsMustUseDatabaseFacade

from nucleus.rules.architecture.planet_cannot_depend_on_driver import PlanetCannotDependOnDriver

from nucleus.rules.architecture.orm_belongs_to_driver import OrmBelongsToDriver

from nucleus.rules.architecture.planet_cannot_know_nucleus_infrastructure import PlanetCannotKnowNucleusInfrastructure

from nucleus.rules.architecture.external_communication_belongs_to_satellites import ExternalCommunicationBelongsToSatellites

from nucleus.exceptions.solar_exception import SolarException


# planet nao pode depender de outro planeta
def test_planet_cannot_depend_on_another_planet():

    dependency = Dependency(
        source="planets.user.repository",
        target="planets.auth.repository",
        file="planets/user/repository.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# repository nao pode depender diretamente de database, driver, orm ou models
def test_repository_cannot_depend_directly_on_database():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.database",
        file="planets/user/repository.py",
        line=3
    )

    rule = RepositoryCannotDependOnDatabase()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# repository pode depender de persistence
def test_repository_can_depend_on_persistence():

    dependency = Dependency(
        source="planets.user.repository",
        target="orbits.database.persistence.persistence",
        file="planets/user/repository.py",
        line=3
    )

    rule = RepositoryMustUsePersistence()

    rule.validate(dependency)


# repository nao pode acessar camada de dados sem passar por persistence
def test_repository_cannot_access_data_layer_without_persistence():

    dependency = Dependency(
        source="planets.user.repository",
        target="orbits.database.models.user_model",
        file="planets/user/repository.py",
        line=3
    )

    rule = RepositoryMustUsePersistence()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# repository nao pode depender diretamente de driver
def test_repository_cannot_depend_on_driver():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.drivers.driver_sqlalchemy",
        file="planets/user/repository.py",
        line=3
    )

    rule = RepositoryMustUsePersistence()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# planet tambem e bloqueado no layout real (orbits.planets.*)
def test_planet_cannot_depend_on_another_planet_in_orbits():

    dependency = Dependency(
        source="orbits.planets.user.service",
        target="orbits.planets.auth.repository",
        file="orbits/planets/user/service.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# planet pode importar seus proprios componentes internos
def test_planet_can_import_its_own_components():

    dependency = Dependency(
        source="planets.user.service",
        target="planets.user.repository",
        file="planets/user/service.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    rule.validate(dependency)


# DENTRO do mesmo Planet, um UseCase pode importar outro UseCase.
# Ex.: vincular_user precisa atualizar o usuario e pode chamar
#      usecase_update_user, pois ambos vivem em planets.user.
def test_use_case_can_import_another_use_case_in_the_same_planet():

    dependency = Dependency(
        source="planets.user.usecases.vincular_user",
        target="planets.user.usecases.usecase_update_user",
        file="planets/user/usecases/vincular_user.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    rule.validate(dependency)


# DENTRO do mesmo Planet, qualquer componente interno e acessivel
# (usecases, entity, repository, controller).
def test_use_case_can_import_internal_components_of_the_same_planet():

    rule = PlanetCannotDependOnPlanet()

    for target, file in (
        ("planets.user.entity", "planets/user/usecases/vincular_user.py"),
        ("planets.user.repository", "planets/user/usecases/vincular_user.py"),
        ("planets.user.controller", "planets/user/usecases/vincular_user.py"),
    ):

        rule.validate(
            Dependency(
                source="planets.user.usecases.vincular_user",
                target=target,
                file=file,
                line=3
            )
        )


# UseCase de um Planet NAO alcanca UseCase de outro Planet.
def test_use_case_cannot_import_a_use_case_from_another_planet():

    dependency = Dependency(
        source="planets.user.usecases.vincular_user",
        target="planets.auth.usecases.update_auth",
        file="planets/user/usecases/vincular_user.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# Para alcancar outro Planet, somente atraves de um Satellite.
def test_use_case_reaches_another_planet_only_through_satellite():

    dependency = Dependency(
        source="planets.user.usecases.vincular_user",
        target="satellites.auth.auth_satellite",
        file="planets/user/usecases/vincular_user.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    rule.validate(dependency)


# planet pode se comunicar com outro planet via satellite
def test_planet_can_communicate_with_another_planet_through_satellite():

    dependency = Dependency(
        source="planets.user.service",
        target="satellites.auth.auth_satellite",
        file="planets/user/service.py",
        line=3
    )

    rule = PlanetCannotDependOnPlanet()

    rule.validate(dependency)


# model nao pode depender de persistence
# pode depender de database (SOLAR-RED-006)
def test_model_cannot_depend_on_persistence():

    dependency = Dependency(
        source="orbits.database.models.user_model",
        target="orbits.database.persistence.persistence",
        file="orbits/database/models/user_model.py",
        line=2
    )

    rule = ModelsCannotDependOnPersistence()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# model nao pode depender de persistence pelo sufixo "_model"
def test_model_with_suffix_cannot_depend_on_persistence():

    dependency = Dependency(
        source="planets.user.user_model",
        target="orbits.database.persistence.users.user_persistency",
        file="planets/user/user_model.py",
        line=2
    )

    rule = ModelsCannotDependOnPersistence()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# model pode depender do database (DTO/ORM via Nucleus.Database)
def test_model_can_depend_on_database():

    dependency = Dependency(
        source="orbits.database.models.user_model",
        target="nucleus.database.database",
        file="orbits/database/models/user_model.py",
        line=2
    )

    rule = ModelsCannotDependOnPersistence()

    rule.validate(dependency)


# model nao pode acessar a tecnologia de ORM diretamente
# deve usar a fachada nucleus.database.database (SOLAR-RED-006)
def test_model_cannot_access_orm_directly():

    dependency = Dependency(
        source="orbits.database.models.user_model",
        target="sqlalchemy",
        file="orbits/database/models/user_model.py",
        line=2
    )

    rule = ModelsMustAccessOrmThroughDatabase()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# model nao pode conhecer o driver diretamente
def test_model_cannot_depend_on_driver():

    dependency = Dependency(
        source="orbits.database.models.user_model",
        target="nucleus.database.drivers.driver_sqlalchemy",
        file="orbits/database/models/user_model.py",
        line=2
    )

    rule = ModelsMustAccessOrmThroughDatabase()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# model pode acessar o ORM atraves da fachada Database
def test_model_can_access_orm_through_database_facade():

    dependency = Dependency(
        source="orbits.database.models.user_model",
        target="nucleus.database.database",
        file="orbits/database/models/user_model.py",
        line=2
    )

    rule = ModelsMustAccessOrmThroughDatabase()

    rule.validate(dependency)


# persistence fora de orbits.database.persistence e violacao
# (modulo de origem)
def test_persistence_outside_orbits_database_is_invalid():

    dependency = Dependency(
        source="planets.user.persistence",
        target="orbits.database.persistence.persistence",
        file="planets/user/persistence.py",
        line=2
    )

    rule = PersistenceBelongsToOrbitsDatabase()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# persistence fora de orbits.database.persistence e violacao
# (modulo de destino)
def test_persistence_target_outside_orbits_database_is_invalid():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.persistence.persistence",
        file="planets/user/repository.py",
        line=2
    )

    rule = PersistenceBelongsToOrbitsDatabase()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# persistence no local canonico e permitida
def test_persistence_in_orbits_database_is_valid():

    dependency = Dependency(
        source="planets.user.repository",
        target="orbits.database.persistence.users.user_persistency",
        file="planets/user/repository.py",
        line=2
    )

    rule = PersistenceBelongsToOrbitsDatabase()

    rule.validate(dependency)


# orbits nao pode acessar o driver diretamente
# deve usar a fachada nucleus.database.database (SOLAR-RED-008)
def test_orbits_cannot_access_driver_directly():

    dependency = Dependency(
        source="orbits.database.persistence.persistence",
        target="nucleus.database.drivers.driver_sqlalchemy",
        file="orbits/database/persistence/persistence.py",
        line=2
    )

    rule = OrbitsMustUseDatabaseFacade()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# orbits nao pode conhecer a interface do driver diretamente
def test_orbits_cannot_access_driver_interface_directly():

    dependency = Dependency(
        source="orbits.database.persistence.persistence",
        target="nucleus.database.drivers.interface.database_driver",
        file="orbits/database/persistence/persistence.py",
        line=2
    )

    rule = OrbitsMustUseDatabaseFacade()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# orbits pode acessar a infraestrutura pela fachada Database
def test_orbits_can_access_database_facade():

    dependency = Dependency(
        source="orbits.database.persistence.persistence",
        target="nucleus.database.database",
        file="orbits/database/persistence/persistence.py",
        line=2
    )

    rule = OrbitsMustUseDatabaseFacade()

    rule.validate(dependency)


# planet nao pode conhecer o driver (modulo de negocio)
def test_planet_cannot_depend_on_driver():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.drivers.driver_sqlalchemy",
        file="planets/user/repository.py",
        line=2
    )

    rule = PlanetCannotDependOnDriver()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# planet nao pode conhecer o driver (layout real)
def test_planet_in_orbits_cannot_depend_on_driver():

    dependency = Dependency(
        source="orbits.planets.user.user_repository",
        target="nucleus.database.drivers.driver_sqlalchemy",
        file="orbits/planets/user/user_repository.py",
        line=2
    )

    rule = PlanetCannotDependOnDriver()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# planet pode acessar o database (nao o driver)
def test_planet_can_depend_on_database():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.database",
        file="planets/user/repository.py",
        line=2
    )

    rule = PlanetCannotDependOnDriver()

    rule.validate(dependency)


# somente o driver pode conhecer a tecnologia de ORM
def test_persistence_cannot_depend_on_orm_technology():

    dependency = Dependency(
        source="orbits.database.persistence.persistence",
        target="sqlalchemy",
        file="orbits/database/persistence/persistence.py",
        line=2
    )

    rule = OrmBelongsToDriver()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# modulo de negocio nao pode conhecer a tecnologia de ORM
def test_business_module_cannot_depend_on_orm_technology():

    dependency = Dependency(
        source="planets.user.repository",
        target="sqlalchemy.orm",
        file="planets/user/repository.py",
        line=2
    )

    rule = OrmBelongsToDriver()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# o driver pode conhecer a tecnologia de ORM
def test_driver_can_depend_on_orm_technology():

    dependency = Dependency(
        source="nucleus.database.drivers.driver_sqlalchemy",
        target="sqlalchemy",
        file="nucleus/database/drivers/driver_sqlalchemy.py",
        line=2
    )

    rule = OrmBelongsToDriver()

    rule.validate(dependency)


# planet nao pode conhecer detalhes internos da infraestrutura do Nucleus
def test_planet_cannot_know_nucleus_infrastructure_details():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.drivers.driver_sqlalchemy",
        file="planets/user/repository.py",
        line=2
    )

    rule = PlanetCannotKnowNucleusInfrastructure()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# planet nao pode conhecer a interface interna do driver
def test_planet_cannot_know_nucleus_driver_interface():

    dependency = Dependency(
        source="orbits.planets.user.user_repository",
        target="nucleus.database.drivers.interface.database_driver",
        file="orbits/planets/user/user_repository.py",
        line=2
    )

    rule = PlanetCannotKnowNucleusInfrastructure()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# planet pode acessar a fachada permitida do Nucleus
def test_planet_can_access_allowed_nucleus_facade():

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.database",
        file="planets/user/repository.py",
        line=2
    )

    rule = PlanetCannotKnowNucleusInfrastructure()

    rule.validate(dependency)


# planet nao pode acessar servico externo diretamente
# a comunicacao deve passar por um Satellite (SOLAR-RED-012)
def test_planet_cannot_access_external_service_directly():

    dependency = Dependency(
        source="planets.user.service",
        target="requests",
        file="planets/user/service.py",
        line=2
    )

    rule = ExternalCommunicationBelongsToSatellites()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# orbits nao pode acessar servico externo diretamente
def test_orbits_cannot_access_external_service_directly():

    dependency = Dependency(
        source="orbits.planets.user.user_service",
        target="httpx",
        file="orbits/planets/user/user_service.py",
        line=2
    )

    rule = ExternalCommunicationBelongsToSatellites()

    with pytest.raises(SolarException):
        rule.validate(dependency)


# satellite pode acessar servico externo
def test_satellite_can_access_external_service():

    dependency = Dependency(
        source="satellites.auth.auth_satellite",
        target="requests",
        file="satellites/auth/auth_satellite.py",
        line=2
    )

    rule = ExternalCommunicationBelongsToSatellites()

    rule.validate(dependency)