# `observatory/audits` — auditorias da SOLAR

Esta pasta concentra os **testes e análises** que observam a aplicação sem
participar dela. É a casa natural desse material: o Observatory é a camada
responsável por verificação, registro, histórico e evidência.

## Estrutura

```text
observatory/audits/
├── estrutural/        Etapas 2 e 3 — métricas, auditoria dos alertas e tracing
├── etapa_4/           desempenho e escalabilidade
└── etapa_5/           segurança e isolamento
```

### `estrutural/`

Contém os scripts e artefatos da análise quantitativa:

- `solar_metrics.py` — grafo, Ca/Ce/I, CBO, LCOM, CC, Halstead, MI e alcançabilidade;
- `revisar_relatorio.py` — auditoria dos 60 alertas do relatório original;
- `auditoria_final/` — pareceres das Etapas 2 e 3, checklist, plano de ação, verificação independente e tracing de runtime;
- CSVs/JSONs e relatório consolidado.

```powershell
py observatory/audits/estrutural/solar_metrics.py --root . --out observatory/audits/estrutural
py observatory/audits/estrutural/revisar_relatorio.py
py observatory/audits/estrutural/auditoria_final/verificacoes_independentes.py
```

### `etapa_4/`

Benchmark de desempenho e escalabilidade, com servidor isolado, SQLite
temporário e dados sintéticos:

```powershell
py observatory/audits/etapa_4/run_benchmark.py
py observatory/audits/etapa_4/diagnose_concurrency.py
```

Documentos: `PLANO_DE_TESTES.md` e `RELATORIO_ETAPA_4.md`.

### `etapa_5/`

Testes de segurança e isolamento, com servidor isolado e dados sintéticos:

```powershell
py observatory/audits/etapa_5/run_security_tests.py
```

Documentos: `PLANO_DE_TESTES.md`, `INVENTARIO_CONTROLES.md`,
`RESULTADOS_TESTES.md`, `REGISTRO_ACHADOS.json` e `RELATORIO_ETAPA_5.md`.

## Relação com o corpus de produção

Os scripts desta pasta são **ferramentas de observação**, não módulos da
aplicação. Por isso, `solar_metrics.py` e `verificacoes_independentes.py`
excluem `observatory/audits/` do corpus de produção: a contagem de 208
módulos, 306 arestas e 553 funções continua sendo a do código da aplicação,
sem os instrumentos de auditoria.

O `ProjectValidator` continua varrendo os arquivos `.py` desta pasta para
garantir que as próprias ferramentas respeitem as regras arquiteturais.
