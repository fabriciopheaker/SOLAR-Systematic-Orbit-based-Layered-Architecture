from pathlib import Path

from nucleus.rules.scanner.architecture_scanner import ArchitectureScanner


def test_scanner():

    # A raiz vem do próprio arquivo de teste. O caminho absoluto
    # `/solar` só existe dentro do container de desenvolvimento e
    # fazia o teste passar apenas naquele ambiente.
    root = Path(__file__).resolve().parents[2]

    scanner = ArchitectureScanner(root)

    dependencies = scanner.scan()

    assert dependencies

