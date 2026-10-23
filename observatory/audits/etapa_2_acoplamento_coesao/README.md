# Etapa 2 — Acoplamento, coesão e dependências

**Pergunta:** como os módulos e classes da SOLAR dependem uns dos outros, e essa
estrutura é compatível com a arquitetura declarada?

**Status:** concluída, com ressalvas documentadas (CBO por AST; tracing sem
requisições HTTP).

## Artefatos

| Artefato                                                                     | Conteúdo                                                                |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| [`RESUMO.md`](RESUMO.md)                                                     | números principais e leitura curta                                      |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md)                               | método, resultados, interpretação e limitações                          |
| [`dados/`](dados/)                                                           | CSVs e JSONs canônicos de acoplamento, coesão, ciclos e alcançabilidade |
| [`scripts/solar_metrics.py`](scripts/solar_metrics.py)                       | cálculo do grafo, fan-in/fan-out, CBO, LCOM e consolidação das métricas |
| [`scripts/revisar_relatorio.py`](scripts/revisar_relatorio.py)               | auditoria item a item dos 60 alertas originais                          |
| [`evidencias/AUDITORIA_ETAPA_2.md`](evidencias/AUDITORIA_ETAPA_2.md)         | auditoria independente da etapa                                         |
| [`evidencias/CHECKLIST_FINAL.md`](evidencias/CHECKLIST_FINAL.md)             | checklist de validação das etapas 2 e 3                                 |
| [`evidencias/PLANO_DE_ACAO.md`](evidencias/PLANO_DE_ACAO.md)                 | pendências e verificações condicionais                                  |
| [`evidencias/runtime_tracing/`](evidencias/runtime_tracing/)                 | tracing de importações em runtime                                       |
| [`evidencias/RELATORIO_CONSOLIDADO.md`](evidencias/RELATORIO_CONSOLIDADO.md) | relatório consolidado original (contexto histórico)                     |
| [`evidencias/LEIA-ME.md`](evidencias/LEIA-ME.md)                             | mapa entre caminhos históricos e atuais                                 |

## Reprodução

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py
py observatory/audits/etapa_2_acoplamento_coesao/scripts/revisar_relatorio.py
py observatory/audits/etapa_2_acoplamento_coesao/evidencias/verificacoes_independentes.py
```

O primeiro comando grava os dados de acoplamento em `dados/` e os dados de
complexidade em `../etapa_3_complexidade/dados/`.

## Leitura de uma frase

A SOLAR tem **208 módulos de produção**, **306 arestas internas** e **0 ciclos
estáticos**; há **1 ciclo dinâmico** entre `Database` e `UserModel`. O
acoplamento é baixo e concentrado em pontos de composição (Kernel) e registro
de regras (`ProjectValidator`). A coesão é interpretável em apenas 39 das 136
classes; nas demais, o LCOM não é aplicável.
