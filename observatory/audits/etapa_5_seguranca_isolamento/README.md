# Etapa 5 — Segurança e isolamento

**Pergunta:** quais controles de segurança estão presentes, quais estão ativos
em runtime e quais riscos são observáveis no estado atual?

**Status:** concluída. Foram executados **33 testes HTTP** contra uma instância
isolada, com dados sintéticos. Nenhuma vulnerabilidade foi confirmada nos
cenários testados; há riscos potenciais e configurações suspeitas.

## Artefatos

| Artefato                                                                               | Conteúdo                                |
| -------------------------------------------------------------------------------------- | --------------------------------------- |
| [`RESUMO.md`](RESUMO.md)                                                               | resultados, achados e conclusão curta   |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md)                                         | método, categorias, achados, limitações |
| [`PLANO_DE_TESTES.md`](PLANO_DE_TESTES.md)                                             | plano original                          |
| [`dados/RESULTADOS_TESTES.json`](dados/RESULTADOS_TESTES.json)                         | resultado bruto dos 33 testes           |
| [`dados/REGISTRO_ACHADOS.json`](dados/REGISTRO_ACHADOS.json)                           | achados estruturados com severidade     |
| [`dados/startup.json`](dados/startup.json)                                             | ambiente da execução                    |
| [`dados/tmp/`](dados/tmp/)                                                             | SQLite temporário e log de erros        |
| [`scripts/run_security_tests.py`](scripts/run_security_tests.py)                       | executor dos testes                     |
| [`scripts/security_server.py`](scripts/security_server.py)                             | servidor isolado                        |
| [`evidencias/INVENTARIO_CONTROLES.md`](evidencias/INVENTARIO_CONTROLES.md)             | inventário de controles                 |
| [`evidencias/RESULTADOS_TESTES.md`](evidencias/RESULTADOS_TESTES.md)                   | tabela legível dos testes               |
| [`evidencias/RELATORIO_ETAPA_5_EXECUCAO.md`](evidencias/RELATORIO_ETAPA_5_EXECUCAO.md) | relatório original                      |

## Reprodução

```powershell
py observatory/audits/etapa_5_seguranca_isolamento/scripts/run_security_tests.py
```

## Leitura de uma frase

Os três headers obrigatórios e o bcrypt funcionam; a validação de presença e de
JSON funciona. Mas o endpoint de criação é **público**, não há validação de tipo
nem limite de tamanho, CSRF/rate limit/brute force/JWT/upload estão inativos, e
404/405 são mascarados como 500. O risco é de exposição e abuso, não de
vulnerabilidade confirmada nos cenários testados.
