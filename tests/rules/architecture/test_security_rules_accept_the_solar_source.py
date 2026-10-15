from pathlib import Path

import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.errors_must_not_leak_internals import (
    ErrorsMustNotLeakInternals
)
from nucleus.rules.architecture.outbound_requests_must_not_use_untrusted_url import (  # noqa: E501
    OutboundRequestsMustNotUseUntrustedUrl
)
from nucleus.rules.architecture.request_data_must_not_become_entities_directly import (  # noqa: E501
    RequestDataMustNotBecomeEntitiesDirectly
)
from nucleus.rules.scanner.error_exposure_scanner import (
    ErrorExposureScanner
)
from nucleus.rules.scanner.mass_assignment_scanner import (
    MassAssignmentScanner
)
from nucleus.rules.scanner.outbound_request_scanner import (
    OutboundRequestScanner
)


def _nucleus_root() -> Path:
    """
    Localiza o diretório nucleus/ do próprio projeto SOLAR.
    """

    for parent in Path(__file__).resolve().parents:

        candidate = parent / "nucleus"

        if candidate.is_dir():
            return candidate

    raise AssertionError("diretório nucleus/ não encontrado")


def _violations(scanner, rule) -> list:

    violations = []

    for occurrence in scanner(_nucleus_root()).scan():

        try:
            rule.validate(occurrence)
        except SolarException:
            violations.append(occurrence)

    return violations


# A regra reprovou o próprio Nucleus (broadcast/broadcast.py e
# storage/drivers/local_storage_driver.py encadeavam a mensagem da
# exceção original na exceção nova). Este teste trava a correção:
# se voltar a aparecer, os locais vêm na asserção.
def test_no_error_leak_in_the_solar_source():

    assert _violations(
        ErrorExposureScanner,
        ErrorsMustNotLeakInternals()
    ) == []


def test_no_mass_assignment_in_the_solar_source():

    assert _violations(
        MassAssignmentScanner,
        RequestDataMustNotBecomeEntitiesDirectly()
    ) == []


# O scanner de SSRF chegou a acusar uma LISTA chamada "requests" em
# rules/scanner/outbound_request_scanner.py. Este teste trava a
# correção (a checagem passou a exigir o método HTTP).
def test_no_untrusted_outbound_request_in_the_solar_source():

    assert _violations(
        OutboundRequestScanner,
        OutboundRequestsMustNotUseUntrustedUrl()
    ) == []
