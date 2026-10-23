# AUDITORIA — ETAPA 2 (Acoplamento e Coesão)

**Arquitetura avaliada:** SOLAR (`nucleus/`, `orbits/`, `observatory/`, `server.py`)
**Data:** 22/10/2026
**Base auditada:** `observatory/audits/estrutural/` (commit `1b39b8e`, árvore de trabalho limpa)
**Verificação independente:** `observatory/audits/estrutural/auditoria_final/verificacoes_independentes.py` → `verificacoes.json`
**Nenhum código-fonte da SOLAR foi alterado.**

---

## 1. Método desta auditoria

1. Leitura integral de `RELATORIO_CONSOLIDADO.md` e dos scripts que o produzem.
2. Conferência de que os artefatos correspondem ao código atual (`git status` limpo; artefatos regerados com hashes comparados).
3. Recálculo independente, com implementação própria, de: contagem de arquivos/classes, CC, Halstead, MI, LCOM1/LCOM4, CBO (5 classes) e acoplamento (4 módulos).
4. Investigação de caminhos alternativos de execução (`importlib`, `pkgutil`, descoberta automática de rotas, `__init__.py` de reexportação, pontos de entrada).
5. Classificação dos itens em **VALIDADO**, **VALIDADO COM RESSALVAS**, **PENDENTE** ou **NÃO APLICÁVEL**.

Separação usada em todo o documento:

- **Fato observado** — número ou comportamento verificável.
- **Interpretação** — leitura técnica do fato.
- **Recomendação** — ação sugerida (nenhuma foi executada).

---

## 2. Corpus e definições efetivamente usadas

| Item                  | Fato observado        | Evidência                                    |
| --------------------- | --------------------- | -------------------------------------------- |
| Módulos de produção   | 208                   | `V1_corpus.production_files`                 |
| Módulos de teste      | 61                    | `git ls`/AST; excluídos do grafo de produção |
| Classes de produção   | 136                   | `V1_corpus.classes_ast` (AST independente)   |
| Arestas internas      | 306                   | `dependencias_internas.csv`                  |
| Densidade do grafo    | 0,71% (306 / 208·207) | cálculo direto                               |
| Arestas intra-camada  | 276 (90,2%)           | `matriz_camadas.csv`                         |
| Arestas entre camadas | 30 (9,8%)             | idem                                         |

**Definições declaradas (e respeitadas):**

- **Ce** = número de módulos internos distintos importados por um módulo.
- **Ca** = número de módulos internos distintos de produção que importam um módulo.
- Testes possuem coluna própria (`fan_in_tests`) e **nunca** entram em Ca/Ce.
- Bibliotecas externas e stdlib não entram em Ca/Ce (234 comandos registrados em `dependencias_externas.csv`).
- **I = Ce / (Ca + Ce)**; indefinida quando `Ca + Ce = 0` (60 módulos: 59 inicializadores sem código + `nucleus.security.token`).

**Observação sobre imports diferidos:** apenas 1 aresta é exclusivamente diferida (`kernel → orbits.routes`, `nucleus/kernel.py:274`). Ela é contada como dependência, porque existe em tempo de execução. Não há imports sob `if TYPE_CHECKING`.

---

## 3. Resultados medidos e verificações

### 3.1 Fan-in e fan-out

| Métrica | N   | Mín. | Mediana | Média | P90 | Máx.   | Módulos com zero |
| ------- | --- | ---- | ------- | ----- | --- | ------ | ---------------- |
| Ce      | 101 | 1    | 3       | 3,03  | 4   | **49** | 107              |
| Ca      | 138 | 1    | 1       | 2,22  | 3   | **38** | 70               |

**Verificação independente (V7):**

| Módulo                               | Ce independente | Ce publicado | Situação                                                           |
| ------------------------------------ | --------------- | ------------ | ------------------------------------------------------------------ |
| `nucleus.rules.project_validator`    | 49              | 49           | idêntico                                                           |
| `nucleus.kernel`                     | 16              | 16           | idêntico                                                           |
| `nucleus.exceptions.solar_exception` | 0               | 0            | idêntico                                                           |
| `nucleus.database.database`          | 3               | 5            | **diferença explicada**: 3 imports estáticos + 2 arestas dinâmicas |

- **Fato:** 0 imports não resolvidos; nenhuma importação de pacote vazio que dependa de reexportação (0 ocorrências).
- **Fato:** não há ciclos no grafo estático (ver 3.4).

**Módulos que merecem atenção (fato):**

| Módulo                               | Ce  | Ca  | I     | Contexto verificado                                                              |
| ------------------------------------ | --- | --- | ----- | -------------------------------------------------------------------------------- |
| `nucleus.rules.project_validator`    | 49  | 2   | 0,961 | instancia explicitamente 29 regras + scanners + relatório                        |
| `nucleus.kernel`                     | 16  | 1   | 0,941 | composition root; monta ambiente, banco, storage, broadcast, middlewares e rotas |
| `nucleus.exceptions.solar_exception` | 0   | 38  | 0,000 | exceção-base do domínio                                                          |
| `nucleus.rules.rule`                 | 0   | 32  | 0,000 | contrato abstrato das regras                                                     |
| `nucleus.database.database`          | 5   | 8   | 0,385 | fachada + 2 arestas dinâmicas                                                    |

**Interpretação:** fan-out alto em `project_validator` e `kernel` é **estrutural e intencional** (registro de regras e composição), não um defeito por si. O risco é de manutenção: cada nova regra exige edição do validador (ponto único de registro). `solar_exception` (Ca = 38) é um hub de exceção — acoplamento aferente alto, mas com contrato estável.

**Recomendação:** nenhuma refatoração. Registrar que o registro de regras é manual e que 49 dependências eferentes é o maior valor do projeto (12× o P90).

---

### 3.2 Instabilidade

| Situação                 | Módulos | Fato                                                          |
| ------------------------ | ------- | ------------------------------------------------------------- |
| I indefinida (`Ca+Ce=0`) | 60      | 59 inicializadores sem código + `nucleus.security.token`      |
| I = 1,0 (`Ca=0`, `Ce>0`) | 10      | inclui `server` (entrada), `kernel` não (Ca=1)                |
| I ≥ 0,8                  | 20      | concentrados em scanners e no validador                       |
| I ≤ 0,2                  | 50      | hubs (`solar_exception`, `rule`, `source_files`, `contracts`) |

**Verificação:** os valores são aritmética direta sobre Ca/Ce validados; a definição de “indefinida” está implementada (campo vazio, não zero).

**Interpretação:** `I` alto em módulos de composição/scanners é esperado. `I` baixo nos contratos e exceções indica estabilidade. Não há valor de corte universal; a leitura é relativa à distribuição.

---

### 3.3 CBO (Coupling Between Objects)

**Método:** aproximação por AST (nomes resolvidos por imports; nomes livres apenas se únicos no projeto; CBO interno = classes do projeto; CBO externo heurístico por símbolo capitalizado).

| Estatística                | Valor             |
| -------------------------- | ----------------- |
| Classes                    | 136               |
| Média                      | 1,54              |
| Mediana                    | 1                 |
| P90                        | 3                 |
| Máximo                     | **15** (`Kernel`) |
| Classes com nomes ambíguos | 0                 |

**Verificação independente (V6):** 5 classes de maior CBO recalculadas com implementação própria — **conjuntos de alvos idênticos**:

| Classe             | CBO independente | CBO publicado | Alvos iguais? |
| ------------------ | ---------------- | ------------- | ------------- |
| `Kernel`           | 15               | 15            | sim           |
| `RequestPipeline`  | 6                | 6             | sim           |
| `ProjectValidator` | 5                | 5             | sim           |
| `Broadcast`        | 4                | 4             | sim           |
| `Server`           | 4                | 4             | sim           |

**Fato:** o CBO de `Kernel` corresponde a 15 classes distintas (Broadcast, InMemoryBroadcast, Database, DriverSQLAlchemy, Environment, 3 exceções, ErrorHandler, RequestPipeline, SecurityHeaders, SecurityPolicy, Identity, LocalStorageDriver, Storage). É um composition root.

**Interpretação:** o valor 15 é um **outlier** (5× o P90) e é explicado pela função de composição. Não há limite universal de CBO; usar “15” como defeito seria indevido.

**Limitações que impedem conclusão absoluta:**

- não resolve tipos (injeção por atributo, fábricas, `getattr`);
- CBO externo é heurístico;
- não mede acoplamento por assinatura/retorno de forma tipada.

**Status:** VALIDADO COM RESSALVAS para o método declarado; PENDENTE para CBO absoluto/tipado.

---

### 3.4 Dependências internas e ciclos

| Grafo                           | Arestas | Ciclos            | SCCs             |
| ------------------------------- | ------- | ----------------- | ---------------- |
| Somente estático (AST)          | 304     | **0**             | 207 para 208 nós |
| Estático + dinâmico verificável | 306     | **1** (tamanho 2) | —                |

**Ciclo (fato, com linhas verificadas):**

```
nucleus/database/database.py:36   MODELS_PACKAGE = "orbits.database.models"
nucleus/database/database.py:138  imported = cls._import_models()
nucleus/database/database.py:157  package = importlib.import_module(cls.MODELS_PACKAGE)
nucleus/database/database.py:167  module = importlib.import_module(f"{cls.MODELS_PACKAGE}.{name}")
orbits/database/models/user_model.py:2   from nucleus.database.database import Database
orbits/database/models/user_model.py:5   class Users(Database.orm):
```

**Evidência de runtime:** com `Database` não inicializado, `import orbits.database.models.user_model` falha com `AttributeError: 'NoneType' object has no attribute 'Column'`; `Database.orm` e `Database.model` são `None` antes de `init()`. Isso confirma que o Model **depende do estado publicado pela fachada no momento do import**.

**Interpretação:** o ciclo é **intencional e controlado** (import tardio, após `Database.init()`), mas existe como dependência bidirecional de módulo. O risco é de ordem de importação: qualquer uso do Model antes de `init()` falha de forma pouco explícita (o `AttributeError` acima).

**Não classificado como defeito.** É uma característica do padrão fachada + modelo declarativo. Deve ser registrado como **risco potencial** de acoplamento temporal, não como violação.

**Fato adicional relevante:** a aresta `kernel → orbits.routes` é **diferida** (dentro de `mount()`), exatamente para permitir a ordem de montagem. Isso reduz o acoplamento em tempo de import, mas não o elimina em runtime.

**Limitação:** não foi executado tracing de importações em uma subida completa da aplicação. A conclusão vale para o grafo estático + imports dinâmicos verificáveis.

---

### 3.5 Alcançabilidade (verificação de “código não alcançável”)

**Método:** BFS nas arestas de produção a partir de `server` e `observatory.solar.__main__`.

| Fato                               | Valor                        |
| ---------------------------------- | ---------------------------- |
| Módulos alcançáveis                | 134 / 208                    |
| Módulos com código não alcançáveis | **15**                       |
| SLOC não alcançável                | **631 (10,08% da produção)** |

**Investigação de caminhos alternativos (feita, não presumida):**

| Possível caminho                           | Resultado                                                                |
| ------------------------------------------ | ------------------------------------------------------------------------ |
| `importlib`/`__import__` em outros módulos | só em `Database` (já modelado)                                           |
| Descoberta automática de rotas             | não existe: `orbits/routes.py` importa os 4 Planets explicitamente       |
| Reexportação em `__init__.py`              | `nucleus/security/__init__.py` e `nucleus/upload/__init__.py` têm 0 byte |
| Referência por nome em configuração/string | nenhuma ocorrência produtiva                                             |
| Uso por testes                             | sim para alguns (não conta como alcançabilidade de produção)             |

**Fatos verificados no código:**

- `Kernel.mount()` instancia `SecurityPolicy`, `RequestPipeline`, `ErrorHandler`, `SecurityHeaders`; **não** instancia `CsrfProtection`, `RateLimiter`, `BruteForceGuard` nem `UrlGuard`.
- `SecurityPolicy` **declara** `csrf_enabled`, `rate_limit_enabled`, `brute_force_enabled`; esses campos são lidos apenas por `csrf_protection.py`, `rate_limiter.py` e `brute_force_guard.py` — justamente os módulos não ligados.
- `nucleus.security.token` não é importado por produção nem por testes (a ocorrência em teste está dentro de string de fixture).
- `ControllerAndUseCaseMustUseNamedContracts` implementa `SOLAR-ROF-003`, é a **única** classe com esse código e **não está entre as 29 regras instanciadas** em `project_validator.py`.
- `orbits.planets.auth/repository/repository.py` está vazio (0 byte).

**Interpretação:** “não alcançável” ≠ “código morto”. Pode ser API preparada, subsistema opcional ou dívida de integração. O que os dados sustentam é: **esses módulos não participam do fluxo executável atual**, e quatro mecanismos de segurança previstos não estão conectados ao ponto de montagem.

**Recomendação:** confirmar a intenção (API pública vs. integração pendente). Não remover nada com base apenas nesta medição.

---

### 3.6 Coesão e LCOM

**Aplicabilidade (fato):**

| Situação                                      | Classes        |
| --------------------------------------------- | -------------- |
| LCOM aplicável                                | **39 (28,7%)** |
| N/A — menos de 2 métodos de instância         | 54             |
| N/A — sem atributos de instância              | 42             |
| N/A — nenhum método de instância usa o estado | 1              |
| **Total**                                     | **136**        |

Categorias: 39 com estado de instância, 50 funcionais/sem estado, 33 sem métodos, 4 com estado único, 4 fachadas `@classmethod` (`Database`, `Storage`, `Broadcast`, `UploadPolicy`), 6 mistas.

**Resultados (N = 39):**

| Métrica | Mín. | Mediana | Média | P90  | Máx. |
| ------- | ---- | ------- | ----- | ---- | ---- |
| LCOM1   | 0    | 3       | 10,82 | 30   | 89   |
| LCOM4   | 1    | 1       | 1,13  | 2    | 3    |
| TCC     | 0,00 | 0,30    | 0,398 | 1,00 | 1,00 |

**Verificação independente (V5):** implementação própria (atributos de instância, chamadas internas, sem reutilizar o script original) sobre as 39 classes aplicáveis → **0 divergências de LCOM1 e 0 de LCOM4**.

**Classes com LCOM4 > 1 (4):**

| Classe                         | LCOM4 | Situação                                                | Classificação                                       |
| ------------------------------ | ----- | ------------------------------------------------------- | --------------------------------------------------- |
| `DriverSQLAlchemy`             | 3     | conexão, vocabulário ORM e sincronização de esquema     | **risco confirmado** de múltiplas responsabilidades |
| `ErrorLog`                     | 2     | caminho de escrita vs. leitura                          | **risco confirmado** (dois usos do mesmo banco)     |
| `Kernel`                       | 2     | `shutdown` não compartilha estado com `mount`/`observe` | **limítrofe** — composition root                    |
| `SecretsMustNotAppearInSource` | 2     | helpers funcionais (`_build_message` só chama `code()`) | **provável artefato** da métrica                    |

**Auditoria do LCOM do relatório original (fato):**

| Classe             | Publicado       | Recalculado                            | Veredito                                      |
| ------------------ | --------------- | -------------------------------------- | --------------------------------------------- |
| `Database`         | 15 (P=15, Q=0)  | `a=0`, 6 `@classmethod` → **N/A**      | **falso positivo**                            |
| `Storage`          | 15 (P=15, Q=0)  | `a=0`, 6 `@classmethod` → **N/A**      | **falso positivo**                            |
| `DatabaseDriver`   | 21 (P=21, Q=0)  | `a=0`, ABC com 7 métodos → **N/A**     | **falso positivo**                            |
| `DriverSQLAlchemy` | 12 (P=27, Q=15) | LCOM1 = 12 (P=24, Q=12)                | **parcial**: valor coincide, detalhamento não |
| `ErrorHandler`     | 11 (P=19, Q=8)  | LCOM1 = 19 (sem `__init__`) / 18 (com) | **não reproduzível** (P+Q=27 ≠ 28)            |

**Interpretação:** LCOM1 é sensível ao número de métodos e não deve ser lido isoladamente. Nas classes de scanner (14 métodos, 1 atributo), LCOM1 = 89 mas LCOM4 = 1 (um único componente conectado por chamadas): **não é baixa coesão**, é estado mínimo com helpers. Os candidatos reais são apenas `DriverSQLAlchemy` e `ErrorLog`.

---

## 4. Consistência e correções aplicadas nesta auditoria

| Item                                                        | Antes                     | Agora                                                                      | Motivo                                                                                |
| ----------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Ordenação de empates em `top_Ce`/`top_Ca`/`top_instability` | variava entre execuções   | determinística                                                             | `set`/`Counter` não garantem ordem em empates; ordenação passou a desempatar por nome |
| Explicação dos 61 arquivos ausentes no CC                   | “61 `__init__.py` vazios” | 59 inits sem código + 1 init só com reexportações + 1 módulo vazio         | verificação arquivo a arquivo                                                         |
| Inits sem arestas                                           | “59”                      | 58 sem arestas; 1 com Ca=1 (`orbits.database.models`)                      | aresta dinâmica da fachada                                                            |
| Categorias de coesão                                        | 41/49/33/9/3/1            | 39/50/33/4/4/6                                                             | tabela estava de uma execução anterior à correção de `cls.x`                          |
| Halstead (Etapa 3)                                          | 548/1.219 (44,95%)        | 561/1.233 (45,50%) na API; 548/1.219 no JSON; 291/553 (52,62%) na produção | colisões de nomes no JSON e separação produção/teste                                  |

Os artefatos CSV/JSON foram regerados duas vezes; após a correção de ordenação, os hashes são idênticos entre execuções.

---

## 5. Limitações da Etapa 2

1. **CBO é aproximação estática.** Não resolve tipos, injeção de dependência, fábricas ou `getattr`. Os 5 casos de maior CBO foram conferidos manualmente, mas o valor absoluto de qualquer classe isolada não é comparável a ferramentas tipadas.
2. **Grafo de imports não é grafo de execução.** Imports diferidos são contados; chamadas dinâmicas não verificáveis não são. A única dependência dinâmica modelada é a de `Database` (literal + varredura de pacote).
3. **Alcançabilidade foi verificada em runtime em dois cenários** (ver Adendo); não há tracing de requisições HTTP nem de outros pontos de entrada além de `server`/CLI.
4. **LCOM não é definido para 71,3% das classes.** A média de LCOM1 sobre todas as classes seria um artefato.
5. **Não há medição de acoplamento por dados** (parâmetros/retornos) nem de profundidade de herança.

---

## 6. Conclusão da Etapa 2

**Pode ser formalmente concluída?** **Sim, com ressalvas registradas.**

Justificativa com evidências:

- Fan-in, fan-out, instabilidade, grafo, ciclos e coesão foram **medidos, reproduzidos e verificados independentemente** (V1, V5, V6, V7, V9).
- As duas únicas ressalvas materiais são o **CBO aproximado** e a **cobertura limitada do tracing de runtime** (dois cenários, sem requisições HTTP). Nenhuma delas impede as conclusões gerais (baixo acoplamento, 1 ciclo intencional, 2 classes com baixa coesão real), mas impedem afirmar valores absolutos de CBO ou generalizar a ausência dos 14 módulos para todos os fluxos.
- Se o protocolo de avaliação exigir **CBO absoluto/tipado**, a etapa fica **pendente** até a verificação P1 do `PLANO_DE_ACAO.md`. Caso o protocolo aceite a aproximação declarada, a etapa está encerrada.

**Pendências que impediriam o encerramento:** apenas `P1` (CBO tipado). O tracing de runtime (P2) foi executado em 22/10/2026, com escopo documentado no Adendo.

---

## 7. Adendo — tracing de importações em runtime (22/10/2026)

**Artefatos:** `observatory/audits/estrutural/auditoria_final/runtime_tracing/` (`trace_imports.py`, três JSON de cenário, `comparacao_alcancabilidade.json`, `RELATORIO_RUNTIME_TRACING.md`).

**Cenários executados:**

| Cenário                                                      | Resultado                                  | Módulos SOLAR |
| ------------------------------------------------------------ | ------------------------------------------ | ------------- |
| A — verificador (`cli.main(["check", ROOT])`)                | saída 0; auditoria `correct`               | 85            |
| B — `import server` + `Kernel.mount()` com SQLite temporário | montagem ok; 3 regras de URL; 5 blueprints | 172           |
| C — import do Model sem `Database.init()`                    | falha `AttributeError`                     | 13            |

**Fatos observados:**

1. `nucleus.database.database` é carregado no evento 226 (via `server.py:3` → `nucleus/kernel.py:19`).
2. `importlib.import_module("orbits.database.models")` ocorre no evento 683 e `...user_model` no 684; a pilha mostra `database.py:167 _import_models` ← `sync` ← `init` ← `kernel.mount`.
3. No momento do import do Model, `Database.orm` já está publicado (`True`); sem `init()`, o import falha com `AttributeError` (cenário C).
4. O audit hook **não vê `importlib.import_module`**; foi necessário um wrapper (limitação documentada).

**Correção da análise de alcançabilidade:**

| Antes (estático)                                         | Depois (runtime)                                                                  |
| -------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 15 módulos com código não alcançáveis, 631 SLOC (10,08%) | **14 confirmados ausentes, 625 SLOC (9,98%)**; `observatory.records` é alcançável |

`observatory.records` (6 SLOC) é carregado como **pacote-pai** de `observatory.records.error_log`, importado por `server`. O grafo estático não materializa a aresta implícita `submódulo → pacote-pai`; por isso o runtime observou **42 pacotes-pai fora do BFS** (41 `__init__.py` vazios + `observatory.records`), nenhum não explicado.

**Escopo:** o único módulo estaticamente alcançável não observado é `observatory.solar.__main__`, porque o caminho `python -m` não foi executado. Os 14 ausentes não foram carregados em nenhum dos três cenários; isso **não prova desuso** em fluxos não exercitados (requisições, jobs, novos Planet).
