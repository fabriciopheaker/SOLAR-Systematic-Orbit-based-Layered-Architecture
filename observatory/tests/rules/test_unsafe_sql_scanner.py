from nucleus.rules.scanner.unsafe_sql_scanner import UnsafeSqlScanner


UNSAFE = """
def find(user_id):

    concatenated = "SELECT * FROM users WHERE id = " + user_id
    interpolated = f"SELECT * FROM users WHERE id = {user_id}"
    formatted = "SELECT * FROM users WHERE id = %s" % user_id
    dotted = "SELECT * FROM users WHERE id = {}".format(user_id)

    return concatenated, interpolated, formatted, dotted
"""

SAFE = """
def find(user_id):

    sql = "SELECT * FROM users WHERE id = :id"

    joined = "SELECT * FROM users " + "WHERE id = :id"

    return sql, joined
"""


def _scan(tmp_path, content: str, path: str = "persistence.py"):

    file = tmp_path / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")

    return UnsafeSqlScanner(tmp_path).scan()


def test_scanner_finds_all_unsafe_forms(tmp_path):

    findings = _scan(tmp_path, UNSAFE)

    kinds = sorted(finding.kind for finding in findings)

    assert kinds == [
        "concatenation",
        "f-string",
        "format",
        "percent",
    ]


# SQL estatico (com ou sem concatenacao de literais) e seguro
def test_scanner_ignores_static_sql(tmp_path):

    assert _scan(tmp_path, SAFE) == []


# o modulo de origem e descrito
def test_scanner_reports_the_module(tmp_path):

    findings = _scan(
        tmp_path,
        UNSAFE,
        "orbits/database/persistence/users/user_persistency.py"
    )

    assert all(
        finding.module
        == "orbits.database.persistence.users.user_persistency"
        for finding in findings
    )
