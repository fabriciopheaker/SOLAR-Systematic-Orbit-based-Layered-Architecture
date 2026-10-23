# Resumo — Etapa 4: desempenho e escalabilidade

## Execução

| Indicador                        | Valor                                                                  |
| -------------------------------- | ---------------------------------------------------------------------- |
| Cenários                         | **12**                                                                 |
| Requisições medidas              | **1.860**                                                              |
| Requisições de aquecimento/setup | **32**                                                                 |
| Total                            | **1.892**                                                              |
| Ambiente                         | Windows 11, Python 3.14.7, Flask 3.1.3, SQLite temporário, `127.0.0.1` |
| Cliente                          | `http.client` + threads (sem `hey`, `wrk`, `ab`, `locust` ou `k6`)     |
| Cenário não executado            | `C_create_c8` (interrompido por erro > 20%)                            |

## Saúde (`GET /solar/health`)

| Concorrência     | Mediana      | Vazão        | Erros |
| ---------------- | ------------ | ------------ | ----- |
| 1 (3 repetições) | 5,45–9,24 ms | 87–124 req/s | 0     |
| 2                | 8,74 ms      | 190,9 req/s  | 0     |
| 4                | 24,66 ms     | 147,0 req/s  | 0     |
| 8                | 37,23 ms     | 204,5 req/s  | 0     |
| 16               | 75,92 ms     | 191,3 req/s  | 0     |

**Leitura:** a latência cresce com a concorrência; a vazão máxima observada foi
~204 req/s (c8) e não cresceu em c16. Não há erro no caminho de saúde.

## Criação (`POST /examples/users`)

| Concorrência | Requisições | Sucessos | Falhas  | Mediana       |
| ------------ | ----------- | -------- | ------- | ------------- |
| 1            | 20          | 20       | 0       | 353,1 ms      |
| 2            | 20          | 18       | 2 (500) | 408,5 ms      |
| 4            | 20          | 14       | 6 (500) | 404,3 ms      |
| 8            | —           | —        | —       | não executado |

**Causa comprovada:** `sqlalchemy.exc.IllegalStateChangeError` em
`commit()`/`rollback()` concorrentes, porque `DriverSQLAlchemy.connect()` cria
uma única `Session` compartilhada. `Session` não é thread-safe.

## Persistência

| Cenário               | Mediana  | Vazão      | Interpretação        |
| --------------------- | -------- | ---------- | -------------------- |
| E-mail duplicado (60) | 10,36 ms | 66,6 req/s | leitura + regra      |
| E-mail inválido (60)  | 6,70 ms  | 78,4 req/s | validação, sem banco |

A diferença de ~3,7 ms é pequena e compatível com variabilidade; **não é
possível separar com confiança** o custo do banco do custo de validação.

## Inicialização

| Etapa                       | Tempo      |
| --------------------------- | ---------- |
| Importação                  | 2.273,5 ms |
| `Kernel.mount()` + ErrorLog | 190,3 ms   |
| `make_server` (bind)        | 18,8 ms    |
| Pronto no processo          | 2.553,6 ms |
| Pronto medido pelo pai      | 2.735,6 ms |

## Conclusão

| Afirmação                                             | Veredito                           |
| ----------------------------------------------------- | ---------------------------------- |
| Há gargalo comprovado na escrita concorrente          | **sustentada**                     |
| O caminho de saúde suporta concorrência 1–16 sem erro | **sustentada**                     |
| O custo de criação é dominado pelo bcrypt             | **sustentada** (353 ms em c1)      |
| A aplicação escala horizontalmente                    | **não testada**                    |
| A vazão observada é a capacidade máxima               | **não sustentada**                 |
| O banco é o gargalo dominante na criação              | **não sustentada** (o hash domina) |
