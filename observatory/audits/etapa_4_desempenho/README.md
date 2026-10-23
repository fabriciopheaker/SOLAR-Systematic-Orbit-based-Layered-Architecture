# Etapa 4 — Desempenho e escalabilidade

**Pergunta:** qual é o comportamento observado da aplicação sob carga controlada,
e onde estão os gargalos?

**Status:** concluída. A execução final tem 12 cenários e 1.860 requisições
medidas. Não é um teste de capacidade máxima nem de escalabilidade horizontal.

## Artefatos

| Artefato                                                                               | Conteúdo                                               |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| [`RESUMO.md`](RESUMO.md)                                                               | resultados principais e conclusão curta                |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md)                                         | método, cenários, resultados, causa e limitações       |
| [`PLANO_DE_TESTES.md`](PLANO_DE_TESTES.md)                                             | plano original de testes                               |
| [`dados/RESULTADOS_CONSOLIDADOS.json`](dados/RESULTADOS_CONSOLIDADOS.json)             | consolidação dos 12 cenários                           |
| [`dados/RESULTADOS_BRUTOS/`](dados/RESULTADOS_BRUTOS/)                                 | amostras brutas por requisição, ambiente e diagnóstico |
| [`dados/startup.json`](dados/startup.json)                                             | tempos de inicialização                                |
| [`dados/tmp/`](dados/tmp/)                                                             | SQLite temporário e log de erros da execução           |
| [`scripts/run_benchmark.py`](scripts/run_benchmark.py)                                 | gerador de carga e consolidação                        |
| [`scripts/bench_server.py`](scripts/bench_server.py)                                   | servidor isolado                                       |
| [`scripts/diagnose_concurrency.py`](scripts/diagnose_concurrency.py)                   | reprodução direta da falha de concorrência             |
| [`scripts/check_failed_writes.py`](scripts/check_failed_writes.py)                     | conferência de escritas perdidas                       |
| [`evidencias/RELATORIO_ETAPA_4_EXECUCAO.md`](evidencias/RELATORIO_ETAPA_4_EXECUCAO.md) | relatório original da execução                         |

## Reprodução

```powershell
py observatory/audits/etapa_4_desempenho/scripts/run_benchmark.py
py observatory/audits/etapa_4_desempenho/scripts/diagnose_concurrency.py
py observatory/audits/etapa_4_desempenho/scripts/check_failed_writes.py
```

## Leitura de uma frase

`GET /solar/health` não falhou em concorrência 1–16; `POST /examples/users` é
dominado pelo bcrypt (mediana ~353 ms em c1) e **falha sob escrita concorrente**
(2/20 em c2, 6/20 em c4, 30%), por causa de uma `Session` SQLAlchemy
compartilhada. O caminho de criação é o gargalo comprovado.
