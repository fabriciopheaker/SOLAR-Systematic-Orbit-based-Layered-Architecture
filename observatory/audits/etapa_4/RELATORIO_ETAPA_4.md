# Relatório — Etapa 4: desempenho e escalabilidade

**Projeto:** SOLAR  
**Data da execução:** 2026-10-23  
**Ambiente:** Windows 11, Python 3.14.7 (CPython), loopback `127.0.0.1`  
**Local:** `observatory/audits/etapa_4/`  
**Escopo:** uma instância local, SQLite temporário, dados sintéticos.

---

## 1. Resumo executivo

A execução final teve **12 cenários** e **1.860 requisições medidas** (mais 32 de aquecimento/setup = **1.892**). Os principais achados:

1. **`GET /solar/health` não apresentou erros** em concorrência 1–16. A mediana subiu de **5,4–9,2 ms** (c1) para **75,9 ms** (c16); a vazão ficou entre **87 e 204 req/s**.
2. **`POST /examples/users` é dominado pelo bcrypt**: mediana de **353 ms** em concorrência 1, contra **6,7 ms** no caminho de e-mail inválido (sem banco e sem hash).
3. **A escrita concorrente falhou**: concorrência 2 teve **2/20 falhas (10%)**; concorrência 4 teve **6/20 (30%)**. O crescimento foi interrompido e **c8 não foi executado**.
4. **A causa foi reproduzida diretamente**: `sqlalchemy.exc.IllegalStateChangeError` na sessão SQLAlchemy compartilhada — `commit()`/`rollback()` concorrentes.
5. **O banco de leitura não foi isolado com segurança**: duplicado teve mediana **10,4 ms** e inválido **6,7 ms**; a diferença é pequena e a amostra é limitada. Não se atribui toda a latência ao banco.
6. **O servidor continuou saudável** após a carga: `GET /solar/health` → 200.

**Conclusão limitada:** há um **gargalo comprovado na escrita concorrente**. O restante é linha de base observada, não capacidade máxima nem escalabilidade horizontal.

---

## 2. Escopo real

| Item         | Constatação                                                                                   |
| ------------ | --------------------------------------------------------------------------------------------- |
| Entrada      | `Kernel.mount()`; servidor de teste Werkzeug                                                  |
| Rotas        | `GET /solar/health`; `POST /examples/users`                                                   |
| Persistência | SQLAlchemy 2.1.1; SQLite em arquivo temporário                                                |
| Sessão       | uma `Session` criada no `DriverSQLAlchemy.connect()` e compartilhada                          |
| Hash         | bcrypt 5.0.0                                                                                  |
| Middleware   | `RequestPipeline`, `SecurityHeaders`, `ErrorHandler`; rate limit/brute force/CSRF não ligados |
| Carga        | gerador próprio `http.client` + threads; não havia `hey`, `wrk`, `ab`, `locust` ou `k6`       |
| Monitor      | CPU/memória via APIs do Windows (`GetProcessTimes`, `GetProcessMemoryInfo`)                   |
| Dados        | sintéticos; nenhum dado pessoal ou segredo real                                               |

**Lacunas:** não há endpoint de leitura de usuários; o custo de leitura só pode ser inferido pelo caminho de e-mail duplicado. Não há requisitos formais de desempenho.

---

## 3. Ferramentas e definições

### 3.1 Ferramentas

| Item       | Versão                                             |
| ---------- | -------------------------------------------------- |
| Python     | 3.14.7                                             |
| Flask      | 3.1.3                                              |
| Werkzeug   | 3.1.9                                              |
| SQLAlchemy | 2.1.1                                              |
| bcrypt     | 5.0.0                                              |
| SQLite     | biblioteca do Python                               |
| pytest     | 9.1.1                                              |
| Servidor   | `werkzeug.serving.make_server(..., threaded=True)` |

### 3.2 Indicadores

- **Latência:** início do envio no cliente até o fim da leitura da resposta; inclui loopback e a primeira conexão de cada worker. Não é o tempo interno isolado da aplicação.
- **Vazão:** requisições concluídas ÷ duração (req/s).
- **Concorrência:** workers com requisição em andamento; não é o total de requisições.
- **Percentis:** P50/P90/P95/P99 pelo método nearest-rank. Com 20 amostras, P99 é praticamente o máximo e tem baixa confiança.
- **Taxa de erro:** respostas inesperadas, timeouts e exceções ÷ total.
- **CPU:** variação do tempo de CPU do servidor ÷ tempo de parede × 100; equivalente a um núcleo, podendo passar de 100%.
- **Memória:** working set do servidor; média e máximo.
- **Inicialização ≠ latência:** a primeira mede importação/montagem/bind; a segunda mede cada requisição pronta.

---

## 4. Cenários executados

| Cenário                       | Teste | Operação         | Conc. | Requisições | Resultado       |
| ----------------------------- | ----- | ---------------- | ----- | ----------- | --------------- |
| `A_referencia_health_r1`      | A     | health           | 1     | 240         | 240×200         |
| `A_referencia_health_r2`      | A     | health           | 1     | 240         | 240×200         |
| `A_referencia_health_r3`      | A     | health           | 1     | 240         | 240×200         |
| `B_baixa_carga_health_c2`     | B     | health           | 2     | 240         | 240×200         |
| `C_health_c4`                 | C/D   | health           | 4     | 240         | 240×200         |
| `C_health_c8`                 | C/D   | health           | 8     | 240         | 240×200         |
| `C_health_c16`                | C/D   | health           | 16    | 240         | 240×200         |
| `A_referencia_create_c1`      | A     | criar usuário    | 1     | 20          | 20×201          |
| `C_create_c2`                 | C/D   | criar usuário    | 2     | 20          | 18×201 + 2×500  |
| `C_create_c4`                 | C/D   | criar usuário    | 4     | 20          | 14×201 + 6×500  |
| `E_persistencia_duplicate_c1` | E     | e-mail duplicado | 1     | 60          | 60×400 esperado |
| `E_validacao_invalid_c1`      | E     | e-mail inválido  | 1     | 60          | 60×400 esperado |

**Não executado:** `C_create_c8`, interrompido porque c4 atingiu 30% de erro, acima do limite de 20%.

**Total:** 1.860 medidas + 32 de aquecimento/setup.

---

## 5. Resultados

### 5.1 Saúde

| Cenário | Conc. | Concl. | Falhas | Duração (s) | Vazão (req/s) | Média (ms) | P50   | P90    | P95    | P99    | CPU (%) | RSS máx. (MB) |
| ------- | ----- | ------ | ------ | ----------- | ------------- | ---------- | ----- | ------ | ------ | ------ | ------- | ------------- |
| A r1    | 1     | 240    | 0      | 2,759       | 87,0          | 11,33      | 9,24  | 20,58  | 28,13  | 36,88  | 68,0    | 93,4          |
| A r2    | 1     | 240    | 0      | 1,940       | 123,7         | 8,02       | 5,45  | 16,80  | 21,65  | 26,98  | 88,6    | 93,6          |
| A r3    | 1     | 240    | 0      | 1,990       | 120,6         | 8,23       | 6,29  | 16,34  | 22,14  | 27,40  | 88,0    | 93,7          |
| B c2    | 2     | 240    | 0      | 1,257       | 190,9         | 10,37      | 8,74  | 18,52  | 24,38  | 26,50  | 139,2   | 103,0         |
| C c4    | 4     | 240    | 0      | 1,632       | 147,0         | 26,84      | 24,66 | 37,69  | 45,23  | 83,26  | 130,2   | 106,8         |
| C c8    | 8     | 240    | 0      | 1,174       | 204,5         | 37,90      | 37,23 | 46,53  | 48,83  | 58,19  | 161,1   | 108,0         |
| C c16   | 16    | 240    | 0      | 1,255       | 191,3         | 80,30      | 75,92 | 104,79 | 107,89 | 111,29 | 166,9   | 108,4         |

**Leitura:** sem erros; latência cresce de forma clara com a concorrência. A vazão máxima observada foi ~204 req/s (c8) e não cresceu em c16. Há variabilidade relevante entre as três repetições c1 (87–124 req/s).

### 5.2 Criação

| Cenário | Conc. | Concl. | Sucessos | Falhas  | Duração (s) | Vazão total | Vazão sucesso | Média (ms) | P50   | P90   | P95   | P99   | CPU (%) | RSS máx. (MB) |
| ------- | ----- | ------ | -------- | ------- | ----------- | ----------- | ------------- | ---------- | ----- | ----- | ----- | ----- | ------- | ------------- |
| A c1    | 1     | 20     | 20       | 0       | 7,125       | 2,81        | 2,81          | 356,1      | 353,1 | 395,8 | 397,1 | 399,8 | 97,4    | 86,7          |
| C c2    | 2     | 20     | 18       | 2 (500) | 4,024       | 4,97        | 4,47          | 397,8      | 408,5 | 442,6 | 564,7 | 564,7 | 183,3   | 89,0          |
| C c4    | 4     | 20     | 14       | 6 (500) | 2,009       | 9,96        | 6,97          | 400,7      | 404,3 | 417,3 | 418,3 | 418,3 | 343,8   | 89,4          |

**Leitura:** o custo por criação é alto (~353–408 ms) e dominado pelo bcrypt. A concorrência aumenta a vazão total, mas introduz falhas; os percentis de sucesso excluem as respostas 500.

### 5.3 Persistência

| Cenário     | Operação             | Concl. | Sucessos | Duração (s) | Vazão | Média | P50   | P90   | P95   | P99   | CPU (%) | RSS máx. |
| ----------- | -------------------- | ------ | -------- | ----------- | ----- | ----- | ----- | ----- | ----- | ----- | ------- | -------- |
| E duplicate | leitura + regra      | 60     | 60       | 0,901       | 66,6  | 14,94 | 10,36 | 28,74 | 30,67 | 41,56 | 57,2    | 87,5     |
| E invalid   | validação, sem banco | 60     | 60       | 0,766       | 78,4  | 12,68 | 6,70  | 28,47 | 29,10 | 30,99 | 53,1    | 89,5     |

**Leitura:** a diferença de mediana (~3,7 ms) é pequena e compatível com variabilidade; **não é possível separar com confiança** o custo do banco. O custo dominante da criação é o hash.

### 5.4 Inicialização

| Etapa                       | Tempo      |
| --------------------------- | ---------- |
| Importação                  | 2.273,5 ms |
| `Kernel.mount()` + ErrorLog | 190,3 ms   |
| `make_server` (bind)        | 18,8 ms    |
| Pronto no processo          | 2.553,6 ms |
| Pronto medido pelo pai      | 2.735,6 ms |

**Não inclui** a verificação arquitetural que o `server.py` completo executa antes de montar.

---

## 6. Análise

### 6.1 Gargalo comprovado: sessão SQLAlchemy compartilhada

**Evidência HTTP:** c2 com 2/20 falhas (10%) e c4 com 6/20 (30%), todas 500. O corpo tinha `code=isce` ou `INTERNAL_ERROR`, sem detalhe interno.

**Evidência direta:** `diagnose_concurrency.py` reproduziu o erro em chamadas concorrentes (resultado registrado em `RESULTADOS_BRUTOS/diagnostico_concorrencia.json`) com:

```text
sqlalchemy.exc.IllegalStateChangeError:
Method 'commit()' can't be called here; method '_prepare_impl()' is already in progress
```

**Causa:** `DriverSQLAlchemy.connect()` cria uma única `Session` compartilhada; `Session` não é thread-safe. O `rollback()` em `UserPersistency.create` também colide.

**Classificação:** **gargalo comprovado na escrita concorrente**. O caminho de saúde não usa a sessão e não falhou.

### 6.2 bcrypt

Criação mediana ~353 ms; inválido ~6,7 ms; duplicado ~10,4 ms. A diferença de ~346 ms é compatível com bcrypt. CPU em c2/c4 chegou a 183%/344%, mostrando uso de múltiplos núcleos.

**Classificação:** custo de CPU **comprovado**; é o principal limitador de vazão da criação, não um defeito.

### 6.3 Saúde

Latência cresce de ~5–9 ms para ~76 ms; vazão máxima ~204 req/s; CPU até 167%; memória ~108 MB. Não houve erro.

**Classificação:** **indício de saturação/limite**, não prova: não foi testado acima de 16, e a vazão já havia estagnado em c16. Não se afirma o ponto de saturação.

### 6.4 Persistência

A diferença duplicado × inválido é pequena e variável. **Inconclusivo** para custo de banco; não atribuir toda a latência à persistência.

### 6.5 Observabilidade

O banco do Observatório registrou 0 erros apesar dos 500. A conexão SQLite do `ErrorLog` é criada na thread principal e usada nas threads; o teste direto confirmou `sqlite3.ProgrammingError`. O `ErrorHandler` silencia a falha. **Limitação comprovada** de trilha de auditoria sob concorrência.

---

## 7. Limitações e cenários não executados

1. Uma instância; sem escalabilidade horizontal.
2. SQLite local; não representa PostgreSQL.
3. Servidor de desenvolvimento Werkzeug; não representa produção.
4. Sem requisitos formais de desempenho.
5. 20 requisições por nível de criação: P99 instável.
6. Falhas excluídas dos percentis de sucesso.
7. Custo de banco não isolado.
8. Observabilidade concorrente limitada.
9. Verificação arquitetural fora do tempo de subida.
10. Logs de requisição ativos no servidor de teste.

**Não executados:** `C_create_c8` (interrompido por segurança), PostgreSQL, múltiplas instâncias, horizontal, rate limit/CSRF, carga longa, comparação histórica.

---

## 8. Reprodutibilidade

```powershell
py observatory/audits/etapa_4/run_benchmark.py
py observatory/audits/etapa_4/run_benchmark.py --smoke
py observatory/audits/etapa_4/diagnose_concurrency.py
py observatory/audits/etapa_4/check_failed_writes.py
```

`bench_server.py` monta `Kernel` real com configuração TEST, SQLite temporário, `.env` temporário e storage temporário; escuta apenas em `127.0.0.1`.

Artefatos brutos em `RESULTADOS_BRUTOS/`; consolidado em `RESULTADOS_CONSOLIDADOS.json`.

---

## 9. Verificação final

| Verificação                      | Resultado                |
| -------------------------------- | ------------------------ |
| Cenários executados              | 12                       |
| Requisições                      | 1.860 medidas + 32 setup |
| Dados brutos                     | CSV/JSON por cenário     |
| Consistência bruta × consolidado | conferida                |
| Saúde após carga                 | 200                      |
| Código de produção alterado      | não                      |
| Testes existentes                | 587 passed               |
| Validador arquitetural           | `correct`                |

### Conclusão

A Etapa 4 foi executada na extensão dos testes realizados. O ambiente permitiu medir a linha de base e comprovar um **gargalo de concorrência na escrita**. Não foi possível validar capacidade máxima, PostgreSQL ou escalabilidade horizontal.
