from nucleus.rules.scanner.controller_auth_check_scanner import (
    ControllerAuthCheckScanner
)


SCATTERED = """
class DocumentController:

    def list(self):
        if not current_user.is_authenticated:
            abort(401)
        if not has_permission("list"):
            abort(403)
        return []
"""

CLEAN = """
class DocumentController:

    @staticmethod
    def list():
        output = list_documents_use_case().execute()
        return DocumentResource.to_object(output)
"""

NOT_A_CONTROLLER = """
class DocumentService:

    def list(self):
        if not current_user.is_authenticated:
            abort(401)
"""


def _scan(tmp_path, content: str):

    controllers = tmp_path / "planets" / "documents" / "controllers"
    controllers.mkdir(parents=True)

    path = controllers / "document_controller.py"
    path.write_text(content, encoding="utf-8")

    return ControllerAuthCheckScanner(tmp_path).scan()


def test_scanner_finds_scattered_auth_checks(tmp_path):

    findings = _scan(tmp_path, SCATTERED)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.controller == "DocumentController"
    assert "current_user" in finding.checks
    assert "has_permission" in finding.checks
    assert "abort(401)" in finding.checks
    assert "abort(403)" in finding.checks


# Controller que nao verifica autenticacao nao tem checks
def test_scanner_reports_no_checks_when_clean(tmp_path):

    finding = _scan(tmp_path, CLEAN)[0]

    assert finding.checks == frozenset()


# classe que nao e Controller nao e descrita
def test_scanner_ignores_non_controller_classes(tmp_path):

    assert _scan(tmp_path, NOT_A_CONTROLLER) == []
