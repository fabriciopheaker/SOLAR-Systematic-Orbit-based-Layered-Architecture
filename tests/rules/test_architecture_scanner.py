from pathlib import Path

from nucleus.rules.scanner.architecture_scanner import ArchitectureScanner


def test_scanner():

    root = Path("/solar")

    scanner = ArchitectureScanner(root)

    dependencies = scanner.scan()

    assert dependencies

