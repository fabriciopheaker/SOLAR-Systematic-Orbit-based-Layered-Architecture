# RELATÓRIO — Tracing de importações em runtime (Etapa 2)

**Data:** 22/10/2026
**Base:** commit `1b39b8e` (árvore de trabalho sem alterações fora de `observatory/audits/`)
**Script:** `observatory/audits/estrutural/auditoria_final/runtime_tracing/trace_imports.py`
**Resultados:** os três JSON desta pasta + `comparacao_alcancabilidade.json`
**Nenhum arquivo de `nucleus/`, `orbits/`, `observatory/`, `server.py`, `tests/` ou `reports/quality/` foi alterado.**

---

## 1. Metodologia

### 1.1 Instrumentação

Cada cenário roda em um **processo separado**, para que `sys.modules` seja limpo e os resultados não se misturem.

| Mecanismo                             | O que registra                                                               | Limitação verificada                                           |
| ------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `sys.addaudithook` no evento `import` | cada importação feita por `import`/`from ... import` (nome do módulo, ordem) | **não vê `importlib.import_module`** (teste controlado abaixo) |
| Wrapper de `importlib.import_module`  | chamadas dinâmicas, pilha de chamada e estado de `Database.orm` no momento   | só cobre chamadas feitas por esse nome                         |
| Diff de `sys.modules` antes/depois    | módulos **efetivamente carregados** (sucesso), com `__file__`                | não distingue tentativa de sucesso; não vê recargas            |

**Limitação confirmada experimentalmente:** o evento de auditoria `import` é emitido pelo `__import__` embutido, não por `importlib.import_module`. Teste:

```powershell
py -c "import sys, importlib; seen=[]; sys.addaudithook(lambda e,a: seen.append(a[0]) if e=='import' else None); importlib.import_module('wave'); print([x for x in seen if 'wave' in x])"
# saída: []
```

Por isso o wrapper foi necessário: sem ele, `orbits.database.models` e `user_model` apareceriam no diff de `sys.modules`, mas **sem ordem nem causalidade**.

### 1.2 Classificação e sanitização

Cada módulo carregado é classificado em:

- **solar** — arquivo sob a raiz, fora de `reports/` e `tests/`;
- **external** — `site-packages`/`dist-packages` (origem reduzida ao pacote de topo);
- **stdlib** — biblioteca padrão, incluindo `DLLs/*.pyd`;
- **builtin** — sem `__file__`;
- **audit** / **test** — scripts de auditoria e testes (excluídos da análise da SOLAR).

Sanitização: caminhos absolutos são substituídos por `<ROOT>`/`<HOME>`; timestamps de arquivos de auditoria são normalizados; **nenhum valor de variável de ambiente, senha ou token é registrado**. O arquivo `.env` temporário e o banco SQLite temporário são apagados ao final do cenário.

### 1.3 Segurança da execução

| Risco                           | Mitigação aplicada                                                                        |
| ------------------------------- | ----------------------------------------------------------------------------------------- |
| Banco de produção               | SQLite em arquivo temporário dentro de `runtime_tracing/tmp/` (apagado ao final)          |
| `.env` do projeto               | arquivo temporário vazio dentro de `tmp/`; `Identity` grava apenas nele; apagado ao final |
| Servidor de rede                | `app.run()` **não** foi chamado; apenas `Kernel.mount()`                                  |
| Arquivo de auditoria do `check` | `audit.audit_directory` redirecionado para `runtime_tracing/check_audit/`                 |
| Escrita fora da pasta           | `git status` fora de `observatory/audits/` permaneceu vazio                               |

---

## 2. Ambiente

| Item                | Valor                                          |
| ------------------- | ---------------------------------------------- |
| Python              | 3.14.7 (CPython)                               |
| Sistema             | Windows 11                                     |
| Flask               | 3.1.3                                          |
| SQLAlchemy          | 2.1.1                                          |
| Alembic             | 1.20.0                                         |
| Driver do cenário B | SQLite (`sqlite+pysqlite`, arquivo temporário) |

---

## 3. Comandos executados

```powershell
# Execução completa (cada cenário em subprocesso) + comparação
py observatory/audits/estrutural/auditoria_final/runtime_tracing/trace_imports.py --all

# Equivalentes individuais
py .../trace_imports.py --scenario verificador
py .../trace_imports.py --scenario bootstrap
py .../trace_imports.py --scenario modelo-isolado
py .../trace_imports.py --compare

# Teste que comprovou a limitação do audit hook
py -c "import sys, importlib; seen=[]; sys.addaudithook(lambda e,a: seen.append(a[0]) if e=='import' else None); importlib.import_module('wave'); print([x for x in seen if 'wave' in x])"
```

Os comandos `--all` foram executados **duas vezes**; os hashes de todos os JSON e do `verificador_stdout.txt` foram idênticos (saída determinística).

---

## 4. Cenários: executados e não executados

### 4.1 Cenário A — Verificador

**Executado.** `observatory.solar.cli.main(["check", ROOT])` — o mesmo caminho de código de `python -m observatory.solar check` (CLI → `run_check` → `ProjectValidator` → `audit.record`).

| Fato                             | Valor                                                                  |
| -------------------------------- | ---------------------------------------------------------------------- |
| Código de saída                  | **0**                                                                  |
| Resultado arquivado              | `correct` (17 verificações, 29 regras, 0 violações)                    |
| Módulos SOLAR carregados         | **85** (78 no conjunto estático alcançável + 7 pacotes-pai implícitos) |
| Externos / stdlib / builtin      | 3 módulos externos (1 pacote: `tzdata`) / 24 / 10                      |
| Eventos de importação observados | 123                                                                    |
| Arquivo de auditoria             | `check_audit/check-<TIMESTAMP>-correct.md` (redirecionado)             |

**Desvio declarado:** não foi usado literalmente `python -m observatory.solar` porque o módulo `__main__` importa a aplicação **antes** de o hook ser instalado. O wrapper instalou o hook e chamou `cli.main`, que é a função executada pelo `__main__`. Consequência: `observatory.solar.__main__` **não** aparece carregado — é a única diferença de escopo.

### 4.2 Cenário B — Bootstrap da aplicação

**Executado.** `import server` (carrega o ponto de entrada sem executar `run()`) e `Kernel(env_file=tmp, config=TEST/sqlite, storage_root=tmp).mount()`.

| Fato                                         | Valor                                                                     |
| -------------------------------------------- | ------------------------------------------------------------------------- |
| `mount()`                                    | **sucesso**                                                               |
| Regras de URL registradas                    | 3                                                                         |
| Blueprints                                   | `orbits`, `orbits.auth`, `orbits.example`, `orbits.solar`, `orbits.user`  |
| `Database.orm` / `Database.model` publicados | `True` / `True`                                                           |
| Módulos SOLAR carregados                     | **172** (131 no conjunto estático alcançável + 41 pacotes-pai implícitos) |
| Externos / stdlib / builtin                  | 381 módulos de 16 pacotes externos / 136 / 21                             |
| Eventos de importação observados             | 731                                                                       |
| Servidor de rede                             | **não iniciado** (`app.run()` não chamado)                                |

Pacotes externos carregados: `alembic`, `bcrypt`, `blinker`, `click`, `colorama`, `dotenv`, `flask`, `itsdangerous`, `jinja2`, `mako`, `markupsafe`, `pygments`, `sqlalchemy`, `typing_extensions`, `tzdata`, `werkzeug`.

### 4.3 Cenário C — Modelo isolado (controle)

**Executado.** `import orbits.database.models.user_model` sem `Database.init()`.

| Fato                     | Valor                                                       |
| ------------------------ | ----------------------------------------------------------- |
| Resultado                | **falha**                                                   |
| Exceção                  | `AttributeError`                                            |
| `Database.orm` no evento | `None` (não publicado)                                      |
| Módulos SOLAR carregados | 13                                                          |
| Módulo não carregado     | `orbits.database.models.user_model` (tentativa sem sucesso) |

### 4.4 Não executado

| Item                                                       | Motivo                                                                     |
| ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| Literal `python -m observatory.solar check`                | importaria `__main__` antes da instrumentação; o equivalente foi executado |
| `Server.run()` / `app.run()`                               | iniciaria servidor de rede; fora do escopo e sem sandbox de porta          |
| Requisições HTTP / handlers                                | exigiria cliente e servidor; fora do escopo desta tarefa                   |
| Outros pontos de entrada (ex.: `orbits/routes.py` isolado) | não são pontos de entrada de processo                                      |
| Windows/Linux com outras versões                           | ambiente único disponível                                                  |

---

## 5. Módulos importados por cenário

Contagens por categoria (fatos):

| Cenário            | SOLAR   | External | Stdlib | Builtin | Total |
| ------------------ | ------- | -------- | ------ | ------- | ----- |
| A — verificador    | 85      | 3        | 24     | 10      | 122   |
| B — bootstrap      | 172     | 381      | 136    | 21      | 710   |
| C — modelo isolado | 13      | 0        | 4      | 1       | 18    |
| União A ∪ B ∪ C    | **175** | —        | —      | —       | —     |

A união de 175 módulos SOLAR é composta por **133 módulos com código** + **42 inicializadores de pacote sem código**. A lista completa, ordenada, está em `imports_runtime_verificador.json` / `imports_runtime_bootstrap.json` (campo `solar_modules`, com `first_import_seq`).

**Fato:** nenhum módulo de `tests/` foi carregado em nenhum cenário; nenhum script de `reports/` foi carregado pela aplicação.

---

## 6. Análise do ciclo `Database` ↔ `user_model`

### 6.1 Linha do tempo observada (cenário B)

| Sequência | Evento                                                         | Evidência                                                                                                                                    |
| --------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 226       | `import nucleus.database.database`                             | `server.py:3` → `nucleus/kernel.py:19`; `Database.orm = None`                                                                                |
| 671       | `importlib.import_module("tzdata.zoneinfo.America")`           | biblioteca externa (não SOLAR)                                                                                                               |
| **683**   | `importlib.import_module("orbits.database.models")`            | pilha: `database.py:157 _import_models` ← `database.py:138 sync` ← `database.py:85 init` ← `kernel.py:162 mount`; `orm` publicado = **True** |
| **684**   | `importlib.import_module("orbits.database.models.user_model")` | pilha: `database.py:167 _import_models` ← `sync` ← `init` ← `mount`; `orm` publicado = **True**                                              |

**Fato:** `nucleus.database.database` já estava em `sys.modules` quando `user_model` foi importado (carregado 458 eventos antes). O import de `user_model` **não gerou novo evento de auditoria para `nucleus.database.database`**, porque o módulo já estava em cache e o evento `import` só é emitido na primeira carga.

### 6.2 Os quatro conceitos, separados

| Conceito                           | Evidência                                                                                                   | Conclusão                                    |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| **Importação observada**           | ambos em `sys.modules`; `first_import_seq` 226 e 684                                                        | confirmado                                   |
| **Relação causal**                 | pilha da chamada dinâmica aponta para `database.py:167 _import_models`                                      | confirmado: quem importa o Model é a fachada |
| **Ciclo no grafo de dependências** | aresta estática `user_model.py:2 → database` + aresta dinâmica `database → user_model`                      | confirmado como ciclo de módulos             |
| **Dependência temporal do estado** | `Database.orm` publicado no momento da chamada; cenário C falha com `AttributeError` quando não há `init()` | confirmado                                   |

**Interpretação:** o ciclo é **real como relação de dependência** e é **intencional** (o Model só pode ser importado após `Database.init()` publicar `orm`/`model`). Não é um defeito por si; é um risco de ordem de importação: uso do Model antes de `init()` falha com erro pouco explícito (`AttributeError`), como o cenário C demonstra.

**Não inferido:** não há evidência de deadlock, recursão infinita ou falha em runtime no caminho normal — o `mount()` completou.

---

## 7. Comparação com a análise estática

### 7.1 Números de referência (recalculados no comparador)

| Métrica                             | Valor                                   |
| ----------------------------------- | --------------------------------------- |
| Módulos de produção                 | 208                                     |
| Módulos de produção **com código**  | 148                                     |
| Alcançáveis no grafo estático (BFS) | 134 (133 com código + 1 inicializador)  |
| Não alcançáveis no grafo estático   | 74 (15 com código + 59 inicializadores) |

### 7.2 Resultado do runtime

| Classificação                                | Módulos                | Explicação                                                                                                                                  |
| -------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Observados e estaticamente alcançáveis       | 132 dos 133 com código | cobertura do caminho real                                                                                                                   |
| Observados **fora** do BFS                   | **42**                 | **42 pacotes-pai carregados implicitamente** (41 `__init__.py` vazios + `observatory.records`, que tem reexportações); nenhum não explicado |
| Estaticamente alcançáveis **não** observados | **1**                  | `observatory.solar.__main__` — ponto de entrada não executado (usamos `cli.main`)                                                           |
| Não alcançáveis com código **observados**    | **1**                  | `observatory.records` — refuta a classificação anterior                                                                                     |
| Não alcançáveis com código **ausentes**      | **14**                 | confirmados ausentes nos dois cenários                                                                                                      |

### 7.3 Correção da Etapa 2

| Antes (análise estática)                                 | Depois (com runtime)                                                                          |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 15 módulos com código não alcançáveis (631 SLOC, 10,08%) | **14 confirmados ausentes (625 SLOC, 9,98%)** + `observatory.records` **alcançável** (6 SLOC) |

**Causa da divergência:** o grafo estático resolve `from observatory.records.error_log import ErrorLog` para o módulo `observatory.records.error_log`, mas **não materializa a importação implícita do pacote-pai** `observatory.records`. O Python carrega o pacote antes do submódulo. O mesmo fenômeno explica os 42 pacotes-pai observados fora do BFS.

**Isso é uma limitação do modelo estático, não um defeito da SOLAR.** Para a próxima medição, recomenda-se adicionar arestas implícitas `submódulo → pacote-pai` ao grafo (ou marcar pacotes como carregados quando um filho for alcançável).

### 7.4 Os 14 módulos confirmados ausentes

Exatamente os mesmos da lista anterior, exceto `observatory.records`:

- `nucleus.upload.file_validator`, `.file_signatures`, `.upload_policy`, `.file_sanitizer`, `.uploaded_file` (5)
- `nucleus.security.url_guard`, `.attempt_tracker`, `.token` (3)
- `nucleus.middleware.csrf_protection`, `.rate_limiter`, `.brute_force_guard` (3)
- `nucleus.rules.architecture.controller_and_usecase_must_use_named_contracts` (1)
- `nucleus.contracts.responsibility_contract` (1)
- `orbits.planets.user.repository.user_repository` (1)

**Fato:** nenhum deles foi carregado em A, B ou C. **Interpretação:** continuam fora do fluxo executável observado; **não** são declarados mortos — pode haver uso em caminhos não exercitados (novas rotas, tarefas futuras, API pública).

---

## 8. Limitações

1. **Dois caminhos de execução apenas.** O verificador e o bootstrap; não há requisições HTTP, tarefas em background, filas ou outros comandos.
2. **Ausência ≠ desuso.** Um módulo não importado nestes cenários pode ser usado em outro fluxo. A conclusão é sobre os cenários executados.
3. **`importlib` não emite audit event.** A limitação foi contornada por wrapper; chamadas dinâmicas feitas por outros mecanismos (`__import__` customizado, `runpy`, plugins) não são cobertas.
4. **Sem recarga de módulos.** `sys.modules` não distingue recarregamentos; não houve `reload` nos cenários.
5. **Ambiente único.** Python 3.14.7 / Windows 11; ordem de imports pode variar em outra plataforma ou versão.
6. **Cenário A com redirecionamento.** O arquivo de auditoria foi redirecionado; o caminho de código é o mesmo, mas o módulo `__main__` não foi importado.
7. **Sem teste de erro.** Falhas de conexão, exceções em handlers e caminhos de erro não foram exercitados (exceto o cenário C, que é justamente uma falha controlada).
8. **Cenário B com SQLite.** O esquema foi criado em arquivo temporário; comportamento de migrations em PostgreSQL não foi testado.

---

## 9. Conclusão objetiva

**Confirmado por execução real:**

1. `Kernel.mount()` completa com SQLite temporário, publica `Database.orm`/`model` e registra 3 regras de URL e 5 blueprints, sem subir servidor.
2. O ciclo `nucleus.database.database ↔ orbits.database.models.user_model` existe como relação de dependência: `Database` carrega primeiro (seq 226); `_import_models` importa `models` (683) e `user_model` (684) via `importlib`; `user_model` importa `Database` no topo (linha 2).
3. A dependência temporal é real: no momento do import do Model, `Database.orm` já está publicado; sem `init()`, o import falha com `AttributeError` (cenário C).
4. Dos 15 módulos antes classificados como não alcançáveis, **14 permanecem ausentes** e **1 (`observatory.records`) é alcançável** por importação implícita de pacote-pai.
5. O grafo estático **subconta pacotes-pai**: 42 inicializadores de pacote foram carregados em runtime fora do BFS (41 vazios + `observatory.records`).
6. O único módulo estaticamente alcançável não observado é `observatory.solar.__main__`, porque o caminho `python -m` não foi executado.

**Permanece inconclusivo:**

- uso dos 14 módulos ausentes em caminhos não exercitados (requisições, jobs, novos Planet, API pública);
- imports dinâmicos que não passem por `importlib.import_module` ou `__import__`;
- comportamento em PostgreSQL, com erro de conexão ou sob concorrência;
- outras versões de Python/plataformas.

**Efeito na Etapa 2:** o item “acoplamento em runtime” deixa de estar pendente e passa a **VALIDADO COM RESSALVAS** (dois cenários, sem requisições). A contagem de módulos não alcançáveis deve ser corrigida de 15 para **14 confirmados**, mantendo a ressalva de que ausência não prova desuso.

---

## 10. Artefatos desta execução

| Arquivo                                    | Conteúdo                                                                    |
| ------------------------------------------ | --------------------------------------------------------------------------- |
| `trace_imports.py`                         | instrumentação, cenários e comparação                                       |
| `imports_runtime_verificador.json`         | cenário A (85 módulos SOLAR, saída 0)                                       |
| `imports_runtime_bootstrap.json`           | cenário B (172 módulos SOLAR, `mount()` ok)                                 |
| `imports_runtime_modelo_isolado.json`      | cenário C (falha `AttributeError`)                                          |
| `comparacao_alcancabilidade.json`          | BFS recalculado, união, classificações e correção 15 → 14                   |
| `verificador_stdout.txt`                   | saída do comando `check`, com caminhos e timestamps normalizados            |
| `check_audit/check-<TIMESTAMP>-correct.md` | registro Markdown produzido pelo próprio `check` (redirecionado)            |
| `tmp/`                                     | diretório de trabalho; vazio ao final (banco e `.env` temporários apagados) |
