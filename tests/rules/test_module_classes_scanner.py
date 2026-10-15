from nucleus.rules.scanner.module_classes_scanner import (
    ModuleClassesScanner
)


def _write(tmp_path, name: str, content: str):

    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return path


def _scan(tmp_path, name: str, content: str):

    _write(tmp_path, name, content)

    return ModuleClassesScanner(tmp_path).scan()


# ---------------------------------------------------------------------
# O que o scanner descreve
# ---------------------------------------------------------------------

def test_classes_are_described_with_lines(tmp_path):

    content = (
        "class UserModel:\n"
        "    pass\n"
        "\n"
        "\n"
        "class DocumentModel:\n"
        "    pass\n"
    )

    module = _scan(
        tmp_path,
        "orbits/database/models/entities.py",
        content
    )[0]

    assert module.module == "orbits.database.models.entities"
    assert module.file == "orbits/database/models/entities.py"
    assert module.names() == ("UserModel", "DocumentModel")
    assert [item.line for item in module.classes] == [1, 5]


# `__init__.py` descreve o proprio pacote
def test_package_init_describes_the_package(tmp_path):

    module = _scan(
        tmp_path,
        "orbits/database/models/__init__.py",
        "class Base:\n    pass\n"
    )[0]

    assert module.module == "orbits.database.models"


# classes aninhadas contam, e a ordem e por LINHA
def test_nested_classes_are_described_in_line_order(tmp_path):

    content = (
        "class Outer:\n"
        "    class Inner:\n"
        "        pass\n"
        "\n"
        "\n"
        "class Depois:\n"
        "    pass\n"
    )

    module = _scan(tmp_path, "package/module.py", content)[0]

    assert module.names() == ("Outer", "Inner", "Depois")
    assert [item.line for item in module.classes] == [1, 2, 6]


# ---------------------------------------------------------------------
# O que o scanner NAO descreve
# ---------------------------------------------------------------------

# arquivo sem classe alguma nao interessa
def test_file_without_classes_is_not_described(tmp_path):

    assert _scan(tmp_path, "config.py", "VALUE = 1\n") == []


# import nao e declaracao
def test_imported_classes_are_not_declared_classes(tmp_path):

    content = (
        "from orbits.database.models.user_model import UserModel\n"
        "from orbits.database.models.document_model import DocumentModel\n"
    )

    assert _scan(tmp_path, "orbits/database/models/__init__.py", content) == []


def test_technical_directories_are_skipped(tmp_path):

    content = "class UserModel:\n    pass\n"

    _write(tmp_path, "__pycache__/cached.py", content)
    _write(tmp_path, ".venv/lib/installed.py", content)
    _write(tmp_path, "build/generated.py", content)

    assert ModuleClassesScanner(tmp_path).scan() == []


def test_exclusions_are_configurable(tmp_path):

    _write(tmp_path, "build/generated.py", "class Generated:\n    pass\n")

    scanner = ModuleClassesScanner(tmp_path, excluded_directories=set())

    assert scanner.scan()[0].file == "build/generated.py"


def test_scanner_without_files_returns_empty(tmp_path):

    assert ModuleClassesScanner(tmp_path).scan() == []