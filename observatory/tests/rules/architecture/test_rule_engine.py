import pytest

from nucleus.rules.rule_engine import RuleEngine
from nucleus.rules.architecture.planet_cannot_depend_on_planet import (
    PlanetCannotDependOnPlanet
)
from nucleus.rules.architecture.repository_cannot_depend_on_database import (
    RepositoryCannotDependOnDatabase
)
from nucleus.rules.architecture.repository_must_use_persistence import (
    RepositoryMustUsePersistence
)
from nucleus.rules.architecture.models_cannot_depend_on_persistence import (
    ModelsCannotDependOnPersistence
)
from nucleus.rules.architecture.models_must_access_orm_through_database import (
    ModelsMustAccessOrmThroughDatabase
)
from nucleus.rules.architecture.persistence_belongs_to_orbits_database import (
    PersistenceBelongsToOrbitsDatabase
)
from nucleus.rules.architecture.orbits_must_use_database_facade import (
    OrbitsMustUseDatabaseFacade
)
from nucleus.rules.architecture.planet_cannot_depend_on_driver import (
    PlanetCannotDependOnDriver
)
from nucleus.rules.architecture.orm_belongs_to_driver import (
    OrmBelongsToDriver
)
from nucleus.rules.architecture.planet_cannot_know_nucleus_infrastructure import (
    PlanetCannotKnowNucleusInfrastructure
)
from nucleus.rules.architecture.external_communication_belongs_to_satellites import (
    ExternalCommunicationBelongsToSatellites
)
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException


def test_rule_engine_executes_registered_rules():

    engine = RuleEngine([
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
    ])

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.database",
        file="planets/user/repository.py",
        line=3
    )

    with pytest.raises(SolarException):
        engine.validate(dependency)