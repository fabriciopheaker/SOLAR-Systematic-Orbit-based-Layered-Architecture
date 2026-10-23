from nucleus.rules.scanner.outbound_request_scanner import (
    OutboundRequestScanner
)


def _scan(tmp_path, content: str):

    path = tmp_path / "satellites" / "http_gateway.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return OutboundRequestScanner(tmp_path).scan()


# ---------------------------------------------------------------------
# Origem confiavel
# ---------------------------------------------------------------------

def test_literal_url_has_no_names(tmp_path):

    finding = _scan(
        tmp_path,
        'requests.get("https://api.exemplo.com/users")\n'
    )[0]

    assert finding.package == "requests"
    assert finding.names == frozenset()


def test_constant_in_fstring_is_the_only_name(tmp_path):

    finding = _scan(
        tmp_path,
        'httpx.get(url=f"{BASE_URL}/users")\n'
    )[0]

    assert finding.names == frozenset({"BASE_URL"})


def test_configuration_source_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        'requests.get(environment.get("API_URL"))\n'
    )[0]

    assert finding.names == frozenset({"environment"})


# ---------------------------------------------------------------------
# Origem nao confiavel
# ---------------------------------------------------------------------

def test_request_source_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        'requests.get(request.args["url"])\n'
    )[0]

    assert "request" in finding.names


def test_bare_variable_is_described(tmp_path):

    finding = _scan(tmp_path, "requests.get(url)\n")[0]

    assert finding.names == frozenset({"url"})


# `self` nao e origem de dado: vale o ATRIBUTO acessado
def test_self_attribute_counts_by_attribute_name(tmp_path):

    finding = _scan(tmp_path, "requests.get(self.base_url)\n")[0]

    assert finding.names == frozenset({"base_url"})


# ---------------------------------------------------------------------
# Fronteiras
# ---------------------------------------------------------------------

def test_call_without_url_is_ignored(tmp_path):

    assert _scan(tmp_path, "requests.Session()\n") == []


def test_client_variable_is_not_a_package(tmp_path):

    assert _scan(tmp_path, "client.get(ADDRESS)\n") == []


# uma variavel local com o nome da biblioteca NAO e a biblioteca:
# a deteccao exige o metodo HTTP, nao so o pacote
def test_local_variable_named_like_the_package_is_ignored(tmp_path):

    content = (
        "requests = []\n"
        "requests.extend(collect())\n"
        "requests.append(build(item))\n"
    )

    assert _scan(tmp_path, content) == []


def test_urlopen_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        "urllib.request.urlopen(target)\n"
    )[0]

    assert finding.package == "urllib"
    assert finding.names == frozenset({"target"})


def test_scanner_without_calls_returns_empty(tmp_path):

    path = tmp_path / "service.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")

    assert OutboundRequestScanner(tmp_path).scan() == []
