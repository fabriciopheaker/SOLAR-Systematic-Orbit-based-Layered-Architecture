import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.routes_must_live_in_route_modules import (
    RoutesMustLiveInRouteModules
)
from nucleus.rules.scanner.route_declaration import RouteDeclaration


def _declaration(
    file: str,
    style: str = RouteDeclaration.REGISTRATION
) -> RouteDeclaration:

    return RouteDeclaration(
        module=file.removesuffix(".py").replace("/", "."),
        file=file,
        line=10,
        style=style,
        mechanism="add_url_rule",
        target="AuthController.login"
    )


# rotas do Planet vivem em planets/<planet>/routes.py
def test_planet_routes_module_is_allowed():

    rule = RoutesMustLiveInRouteModules()

    rule.validate(
        _declaration("planets/auth/routes.py")
    )


# layout real: orbits/planets/<planet>/routes.py
def test_planet_routes_module_in_orbits_is_allowed():

    rule = RoutesMustLiveInRouteModules()

    rule.validate(
        _declaration("orbits/planets/auth/routes.py")
    )


# composicao central em orbits/routes.py
def test_central_orbits_routes_module_is_allowed():

    rule = RoutesMustLiveInRouteModules()

    rule.validate(
        _declaration("orbits/routes.py")
    )


# pacote orbits/routes/ nao e a estrutura definida (deve ser routes.py)
def test_orbits_routes_package_file_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("orbits/routes/api.py")
        )


# rotas do Planet tambem usam routes.py
# (estrutura: routes.py, repository.py, controller.py, usecases/)
def test_planet_use_case_module_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("planets/user/usecases/create_user.py")
        )


# controller do Planet nao declara rotas
# (estrutura: routes.py, repository.py, controller.py, usecases/)
def test_planet_controller_module_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("planets/user/controller.py")
        )


# rota declarada em service do Planet e rejeitada
def test_route_in_service_module_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("planets/user/service.py")
        )


# rota declarada dentro de um Controller e rejeitada
# (o Planet usa controller.py na raiz)
def test_route_in_controller_module_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("planets/user/controllers/user_controller.py")
        )


# rota declarada em repository do Planet e rejeitada
def test_route_in_repository_module_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("planets/auth/repository.py")
        )


# nome de arquivo nao reconhecido (route.py) e rejeitado
def test_unknown_route_filename_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("planets/auth/route.py")
        )


# rota por decorator tambem precisa estar em modulo de rotas
def test_decorator_route_outside_routes_module_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration(
                "planets/auth/service.py",
                RouteDeclaration.DECORATOR
            )
        )


# arquivo fora de planets/**/routes.py e orbits/routes.py e rejeitado
def test_route_outside_known_locations_is_rejected():

    rule = RoutesMustLiveInRouteModules()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration("orbits/database/persistence/persistence.py")
        )
