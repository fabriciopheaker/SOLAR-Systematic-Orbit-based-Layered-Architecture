# Relatório técnico — Etapa 4: desempenho e escalabilidade

**Projeto:** SOLAR
**Data da execução:** 2026-10-23
**Ambiente:** Windows 11, Python 3.14.7 (CPython), loopback `127.0.0.1`
**Servidor:** Werkzeug `make_server(..., threaded=True)`
**Persistência:** SQLAlchemy 2.1.1 com SQLite em arquivo temporário
**Código de produção alterado:** não

---

## 1. Objetivo e escopo

O objetivo é medir o comportamento observado de dois caminhos HTTP sob carga
controlada:

- `GET /solar/health` — caminho sem banco e sem hash;
- `POST /examples/users` — caminho com validação, bcrypt, escrita e leitura.

A execução responde a perguntas limitadas:

1. Como a latência e a vazão variam com a concorrência?
2. Onde estão os erros?
3. Qual é o custo de inicialização?

**Não** responde:

- qual é a capacidade máxima;
- se a aplicação escala horizontalmente;
- se o desempenho é “bom” sem requisitos formais;
- se o comportamento se mantém em outro hardware, sistema operacional ou banco.

---

## 2. Método

### 2.1 Isolamento

- Processo servidor separado, iniciado por `bench_server.py`.
- Banco SQLite em arquivo temporário, recriado a cada execução.
- `storage` e `.env` temporários.
- Dados sintéticos; nenhum dado pessoal ou segredo real.
- Monitor de CPU/memória por APIs do Windows (`GetProcessTimes`,
  `GetProcessMemoryInfo`).

### 2.2 Métricas

| Métrica      | Definição                                                              |
| ------------ | ---------------------------------------------------------------------- |
| Latência     | envio do cliente até fim da leitura da resposta (inclui loopback)      |
| Vazão        | requisições concluídas ÷ duração                                       |
| Concorrência | workers com requisição em andamento                                    |
| Percentis    | P50/P90/P95/P99 por nearest-rank                                       |
| Taxa de erro | respostas inesperadas, timeouts e exceções ÷ total                     |
| CPU          | tempo de CPU do servidor ÷ tempo de parede × 100 (pode passar de 100%) |
| Memória      | working set do servidor (média e máximo)                               |

Com 20 amostras, o P99 é praticamente o máximo e tem baixa confiança.

### 2.3 Cenários

| Cenário                        | Teste | Operação         | Conc.  | Requisições |
| ------------------------------ | ----- | ---------------- | ------ | ----------- |
| `A_referencia_health_r1/r2/r3` | A     | health           | 1      | 240 cada    |
| `B_baixa_carga_health_c2`      | B     | health           | 2      | 240         |
| `C_health_c4/c8/c16`           | C/D   | health           | 4/8/16 | 240 cada    |
| `A_referencia_create_c1`       | A     | criar usuário    | 1      | 20          |
| `C_create_c2`                  | C/D   | criar usuário    | 2      | 20          |
| `C_create_c4`                  | C/D   | criar usuário    | 4      | 20          |
| `E_persistencia_duplicate_c1`  | E     | e-mail duplicado | 1      | 60          |
| `E_validacao_invalid_c1`       | E     | e-mail inválido  | 1      | 60          |

`C_create_c8` não foi executado porque c4 atingiu 30% de erro, acima do limite
de segurança de 20%.

---

## 3. Resultados

### 3.1 Saúde

| Cenário | Conc. | Concl. | Falhas | Vazão | Mediana | P95    | CPU    | RSS máx. |
| ------- | ----- | ------ | ------ | ----- | ------- | ------ | ------ | -------- |
| A r1    | 1     | 240    | 0      | 87,0  | 9,24    | 28,13  | 68,0%  | 93,4 MB  |
| A r2    | 1     | 240    | 0      | 123,7 | 5,45    | 21,65  | 88,6%  | 93,6 MB  |
| A r3    | 1     | 240    | 0      | 120,6 | 6,29    | 22,14  | 88,0%  | 93,7 MB  |
| B c2    | 2     | 240    | 0      | 190,9 | 8,74    | 24,38  | 139,2% | 103,0 MB |
| C c4    | 4     | 240    | 0      | 147,0 | 24,66   | 45,23  | 130,2% | 106,8 MB |
| C c8    | 8     | 240    | 0      | 204,5 | 37,23   | 48,83  | 161,1% | 108,0 MB |
| C c16   | 16    | 240    | 0      | 191,3 | 75,92   | 107,89 | 166,9% | 108,4 MB |

### 3.2 Criação

| Cenário | Conc. | Concl. | Sucessos | Falhas  | Vazão total | Mediana | P95   |
| ------- | ----- | ------ | -------- | ------- | ----------- | ------- | ----- |
| A c1    | 1     | 20     | 20       | 0       | 2,81        | 353,1   | 397,1 |
| C c2    | 2     | 20     | 18       | 2 (500) | 4,97        | 408,5   | 564,7 |
| C c4    | 4     | 20     | 14       | 6 (500) | 9,96        | 404,3   | 418,3 |

### 3.3 Persistência

| Cenário          | Concl. | Sucessos | Vazão | Mediana | P95   |
| ---------------- | ------ | -------- | ----- | ------- | ----- |
| E-mail duplicado | 60     | 60       | 66,6  | 10,36   | 30,67 |
| E-mail inválido  | 60     | 60       | 78,4  | 6,70    | 29,10 |

### 3.4 Inicialização

| Etapa                       | Tempo      |
| --------------------------- | ---------- |
| Importação                  | 2.273,5 ms |
| `Kernel.mount()` + ErrorLog | 190,3 ms   |
| `make_server` (bind)        | 18,8 ms    |
| Pronto no processo          | 2.553,6 ms |
| Pronto medido pelo pai      | 2.735,6 ms |

Não inclui a verificação arquitetural que o `server.py` completo executa antes
de montar.

---

## 4. Achado principal: sessão SQLAlchemy compartilhada

### 4.1 Evidência HTTP

- c2: **2/20 falhas (10%)**;
- c4: **6/20 falhas (30%)**;
- todas as falhas foram HTTP 500 com `code=isce` ou `INTERNAL_ERROR`, sem
  detalhe interno.

### 4.2 Evidência direta

`diagnose_concurrency.py` reproduziu:

```text
sqlalchemy.exc.IllegalStateChangeError:
Method 'commit()' can't be called here; method '_prepare_impl()' is already in progress
```

### 4.3 Causa

`DriverSQLAlchemy.connect()` cria uma única `Session` compartilhada.
`Session` não é thread-safe; `commit()` e `rollback()` concorrentes colidem.
O `rollback()` em `UserPersistency.create` também participa da colisão.

### 4.4 Classificação

**Gargalo comprovado na escrita concorrente.** O caminho de saúde não usa a
sessão e não falhou.

---

## 5. O que os números não permitem concluir

1. **Capacidade máxima:** a carga foi limitada e interrompida por erro.
2. **Escalabilidade horizontal:** um único processo, uma única instância.
3. **Custo do banco:** a diferença duplicado × inválido é pequena e tem
   variabilidade.
4. **Generalização:** hardware, sistema e SQLite locais.
5. **Requisito de desempenho:** não há SLO formal; os números são linha de base.

---

## 6. Recomendações condicionadas

| Achado                      | Ação sugerida                                    | Não fazer                               |
| --------------------------- | ------------------------------------------------ | --------------------------------------- |
| Sessão compartilhada        | usar sessão por thread/requisição ou pool seguro | aumentar concorrência antes de corrigir |
| Custo do bcrypt             | manter; é intencional                            | remover hash para “melhorar” latência   |
| 404/405 mascarados como 500 | corrigir o handler (ver etapa 5)                 | tratar como falha de desempenho         |
| Ausência de SLO             | definir metas antes de comparar                  | declarar “bom” sem critério             |

---

## 7. Reprodução

```powershell
py observatory/audits/etapa_4_desempenho/scripts/run_benchmark.py
py observatory/audits/etapa_4_desempenho/scripts/diagnose_concurrency.py
py observatory/audits/etapa_4_desempenho/scripts/check_failed_writes.py
```

Artefatos:

- `dados/RESULTADOS_CONSOLIDADOS.json`
- `dados/RESULTADOS_BRUTOS/*.csv` e `*.json`
- `dados/startup.json`
- `dados/tmp/bench.sqlite`

---

## 8. Veredito da etapa

| Afirmação                               | Veredito                           |
| --------------------------------------- | ---------------------------------- |
| O caminho de saúde não falhou em c1–c16 | **sustentada**                     |
| A escrita concorrente falha             | **sustentada** (c2/c4)             |
| A causa é a sessão compartilhada        | **sustentada** (reprodução direta) |
| O bcrypt domina o custo de criação      | **sustentada** (~353 ms em c1)     |
| A aplicação é escalável horizontalmente | **não testada**                    |
| O desempenho é “bom”                    | **não sustentada** sem SLO         |
