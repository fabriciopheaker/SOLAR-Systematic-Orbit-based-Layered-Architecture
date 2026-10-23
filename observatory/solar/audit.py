"""
Auditoria da verificação arquitetural.

Quando `python observatory/solar check` roda, o resultado é
registrado em Markdown dentro de
`observatory/audits/etapa_1_conformidade/evidencias/check/` —
`correct` ou `violation`.

Por que registrar SEMPRE: o registro da última execução é a
garantia de que ela aconteceu e de como terminou. Se só a violação
gerasse arquivo, "nenhum arquivo novo" seria ambíguo — tanto pode
significar "está tudo certo" quanto "ninguém rodou a verificação".

Por que registrar: uma verificação que só aparece no terminal
desaparece quando o terminal fecha. O arquivo fica — dá para
comparar duas execuções, anexar em uma revisão e acompanhar se a
dívida está diminuindo.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from nucleus.rules.report import ProjectReport


# Os três segmentos do caminho de auditoria, um por constante: o
# diretório é montado a partir deles, e mudar de lugar é editar um lugar
# só.
OBSERVATORY_DIRECTORY = "observatory"
AUDITS_DIRECTORY = "audits"
STAGE_DIRECTORY = "etapa_1_conformidade"
EVIDENCE_DIRECTORY = "evidencias"
AUDIT_DIRECTORY = "check"

# `check-2026-10-06-115425-correct.md`. O prefixo mantém o arquivo
# agrupado com o comando que o gerou.
FILENAME_PREFIX = "check"
FILENAME_SUFFIX = ".md"


# Fuso de São Paulo — o registro é lido por quem opera a aplicação, e a
# hora local é a que faz sentido para essa pessoa.
try:
    TIME_ZONE = ZoneInfo("America/Sao_Paulo")
    TIME_ZONE_LABEL = "America/Sao_Paulo"

# A base IANA pode faltar em imagem mínima. `UTC-03:00` é o MESMO
# deslocamento de São Paulo hoje (o Brasil não usa mais horário de
# verão), então o carimbo continua certo — só o rótulo muda, e é ele que
# diz qual dos dois caminhos foi usado.
except ZoneInfoNotFoundError:

    TIME_ZONE = timezone(timedelta(hours=-3))
    TIME_ZONE_LABEL = "UTC-03:00"

# Ordenável: dois arquivos lado a lado ficam em ordem cronológica.
TIMESTAMP_FORMAT = "%Y-%m-%d-%H%M%S"
DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"


def audit_directory(root: Path) -> Path:
    """
    Diretório de auditoria do projeto verificado.

    Fica na etapa de conformidade da camada de auditoria:
    `observatory/audits/etapa_1_conformidade/evidencias/check/`.
    """

    return (
        Path(root)
        / OBSERVATORY_DIRECTORY
        / AUDITS_DIRECTORY
        / STAGE_DIRECTORY
        / EVIDENCE_DIRECTORY
        / AUDIT_DIRECTORY
    )


def display_path(path: Path) -> Path:
    """
    Caminho do registro na forma em que ele deve ser MOSTRADO.

    Relativo ao diretório atual quando possível — quem lê a linha é
    uma pessoa, e `observatory/audits/etapa_1_conformidade/evidencias/check/...`
    é mais legível que o caminho absoluto. Fora do diretório atual (o `check` foi rodado
    apontando para outro projeto), o absoluto é a única informação
    útil.
    """

    try:
        return path.relative_to(Path.cwd())

    # `ValueError` = o arquivo ficou fora do diretório atual.
    except ValueError:
        return path


def record(
    report: ProjectReport,
    root: Path,
    generated_at: datetime | None = None
) -> Path:
    """
    Registra o resultado e devolve o caminho do arquivo.

    Grava SEMPRE — `correct` ou `violation`. Sem horário informado,
    usa a hora de São Paulo.
    """

    # `generated_at` injetável: o teste fixa o horário para poder
    # afirmar o NOME do arquivo, que carrega o momento.
    moment = generated_at or datetime.now(TIME_ZONE)
    directory = audit_directory(root)

    # `parents=True` cria a árvore do zero (o projeto pode nunca ter
    # rodado o check); `exist_ok=True` porque na segunda execução ela já
    # existe — e isso não é erro.
    directory.mkdir(parents=True, exist_ok=True)

    # O caminho é escolhido ANTES de escrever, para resolver a colisão de
    # nome (ver `_available_path`).
    path = _available_path(directory, moment, report.status())

    # `encoding="utf-8"` explícito: o texto tem acento, e o padrão do
    # sistema não é confiável — no Windows seria `cp1252`.
    path.write_text(
        render(report, root, moment),
        encoding="utf-8"
    )

    return path


def record_violation(
    report: ProjectReport,
    root: Path,
    generated_at: datetime | None = None
) -> Path | None:
    """
    Registra APENAS quando há violação.

    Política diferente da de `record`, e a diferença é QUEM pediu a
    verificação:

        `record`            o comando `check` — a pessoa pediu a
                            verificação, então o registro é a
                            resposta, e vale mesmo quando está tudo
                            certo;

        `record_violation`  a subida do servidor — a verificação roda
                            sozinha, sem ninguém pedir. Gravar a cada
                            subida encheria o diretório de arquivos
                            idênticos e afogaria o registro que
                            importa: o da violação.

    Devolve o caminho do arquivo, ou `None` quando não havia nada a
    registrar.
    """

    if report.is_clean():
        return None

    # Reusa o registro inteiro: o que muda é SÓ a decisão de gravar.
    return record(report, root, generated_at)


def render(
    report: ProjectReport,
    root: Path,
    generated_at: datetime
) -> str:
    """
    Monta o Markdown da auditoria.
    """

    # Lista de pedaços juntados por `\n`, com as linhas vazias no meio:
    # é o que separa um bloco do outro no Markdown renderizado.
    #
    # A seção de violações aparece SEMPRE, mesmo vazia: o documento tem
    # estrutura fixa, e nem quem lê nem um diff precisam adivinhar.
    return "\n".join([
        "# SOLAR — auditoria da verificação arquitetural",
        "",
        _summary(report, root, generated_at),
        "",
        "## Verificações",
        "",
        _checks_table(report),
        "",
        "## Violações",
        "",
        _violations(report),
    ])


def _summary(
    report: ProjectReport,
    root: Path,
    generated_at: datetime
) -> str:
    """
    Resumo em tabela: o que foi verificado e o que saiu.
    """

    # Pares rótulo/valor em vez de linhas prontas: a formatação da tabela
    # fica em um lugar só, na junção abaixo.
    rows = (
        # O RESULTADO é a primeira linha — é o que se procura ao abrir.
        ("resultado", report.status()),
        (
            "gerado em",
            f"{generated_at.strftime(DISPLAY_FORMAT)} "
            f"({TIME_ZONE_LABEL})"
        ),
        ("raiz verificada", str(Path(root).resolve())),
        ("verificações", str(len(report.results))),
        ("regras", str(report.rules)),
        ("violações", str(len(report.violations))),
        ("regras violadas", str(report.rules_violated())),
    )

    # Tabela sem cabeçalho (`| | |`): os rótulos já estão na primeira
    # coluna, e um cabeçalho repetindo isso só ocuparia espaço.
    return "\n".join(
        ["| | |", "| --- | --- |"]
        + [f"| {label} | {value} |" for label, value in rows]
    )


def _checks_table(report: ProjectReport) -> str:
    """
    Status de CADA verificação, inclusive as que passaram.

    Saber o que foi verificado vale tanto quanto saber o que
    falhou: é o que mostra que a regra está de fato rodando.
    """

    # Percorre `results` (e não `violations`): a tabela mostra TAMBÉM as
    # verificações que passaram.
    return "\n".join(
        ["| Verificação | Status |", "| --- | --- |"]
        + [
            f"| {result.name} | {result.status()} |"
            for result in report.results
        ]
    )


def _violations(report: ProjectReport) -> str:
    """
    O que fazer: agrupado por regra, com o local de cada caso.
    """

    # Dois `for` encadeados: um por regra e outro pelos DOIS pedaços de
    # cada regra (o bloco e uma linha em branco). Sem a linha em branco
    # entre blocos, o título de uma regra colaria no texto da anterior.
    #
    # `.rstrip()` tira a última linha em branco, que não serve para nada
    # no fim do arquivo.
    return "\n".join(
        block
        for rule, violations in report.by_rule().items()
        for block in (
            _rule_block(rule, violations),
            "",
        )
    ).rstrip()


def _rule_block(rule, violations) -> str:
    """
    Uma regra e os seus casos.
    """

    # Título com a contagem entre parênteses: quem lê a auditoria de
    # relance vê QUANTOS casos a regra tem antes de ler cada um.
    lines = [
        f"### {rule} · {violations[0].description} "
        f"({len(violations)})",
        "",
    ]

    for violation in violations:

        # Local em negrito e mensagem indentada abaixo: os dois espaços
        # no início fazem o Markdown entender a mensagem como
        # continuação do mesmo item de lista.
        lines.append(f"- **{violation.location or '—'}**")
        lines.append(f"  {violation.message}")

    return "\n".join(lines)


def _available_path(
    directory: Path,
    moment: datetime,
    status: str
) -> Path:
    """
    Caminho livre para o registro.

    O nome carrega o MOMENTO e o RESULTADO: o arquivo mais recente
    diz, sem precisar abrir, se a última verificação passou.

    Duas execuções no mesmo segundo não podem se sobrescrever: um
    registro de auditoria perdido é pior do que um nome feio.
    """

    stamp = moment.strftime(TIMESTAMP_FORMAT)
    name = f"{FILENAME_PREFIX}-{stamp}-{status}"

    candidate = directory / f"{name}{FILENAME_SUFFIX}"

    # Começa em 2 porque o sufixo `-2` é o SEGUNDO arquivo do mesmo
    # segundo; o primeiro não leva número.
    counter = 2

    # Laço em vez de teste único: três execuções no mesmo segundo pedem
    # `-2` e `-3`.
    while candidate.exists():

        candidate = (
            directory
            / f"{name}-{counter}{FILENAME_SUFFIX}"
        )

        counter += 1

    return candidate
