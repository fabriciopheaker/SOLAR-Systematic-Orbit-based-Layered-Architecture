# Capítulo 5A — Catálogo: acoplamento, CBO e ciclos

> **Como usar este capítulo:** cada seção segue a mesma ficha de 18 itens. As seções 5.5 a 5.9 estão no [Capítulo 5C](capitulo-05c-complexidade-e-tamanho.md); 5.10 e 5.12 estão no [Capítulo 5B](capitulo-05b-coesao-e-alcance.md); 5.13 está no [Capítulo 5D](capitulo-05d-analises-adicionais.md).

**Convenção de leitura:** “módulo” = arquivo Python importável; “classe” = definição de classe; “dependência interna” = importação de outro módulo do projeto, excluindo bibliotecas externas e testes.

---

## 5.1 Fan-in (Ca)

| #   | Campo                               | Conteúdo                                                                                                                                                                                                 |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Número de dependências recebidas; acoplamento aferente                                                                                                                                                   |
| 2   | Nome original                       | _Fan-in_; _afferent coupling_                                                                                                                                                                            |
| 3   | Sigla                               | **Ca** — _afferent coupling_ (acoplamento aferente)                                                                                                                                                      |
| 4   | Categoria                           | dependências e acoplamento                                                                                                                                                                               |
| 5   | O que é, em linguagem simples       | Quantos módulos “apontam para” este módulo. É como contar quantas estradas chegam a uma cidade.                                                                                                          |
| 6   | O que mede exatamente               | Número de **módulos internos distintos de produção** que importam o módulo analisado. Importações repetidas do mesmo módulo contam uma vez. Testes são contados em coluna separada.                      |
| 7   | Por que é importante                | Um Ca alto indica um ponto central: mudanças no contrato podem afetar muitos consumidores. Um Ca baixo pode indicar módulo folha, ponto de entrada ou código não utilizado.                              |
| 8   | Como é calculado                    | Constrói-se o grafo de imports; para cada aresta `origem → destino`, incrementa-se `Ca(destino)`. O valor é a contagem de origens distintas.                                                             |
| 9   | Como interpretar                    | Alto: hub/reutilização/impacto. Baixo: folha/entrada/possível falta de uso. Nenhum dos dois é “bom” ou “ruim” sem contexto.                                                                              |
| 10  | Cenário favorável                   | Um contrato estável (exceção-base, interface) com Ca alto e poucas mudanças.                                                                                                                             |
| 11  | Cenário potencialmente desfavorável | Um módulo de detalhe (implementação) com Ca alto: qualquer mudança afeta muitos pontos.                                                                                                                  |
| 12  | Exemplo numérico                    | Se A→X, B→X e C→X, então Ca(X) = 3. Se A importa X duas vezes, continua 3.                                                                                                                               |
| 13  | Exemplo no SOLAR                    | `nucleus.exceptions.solar_exception` tem Ca = 38; `nucleus.rules.rule` tem 32; `source_files` tem 17. Há 70 módulos com Ca = 0. O fan-in de testes de `solar_exception` é 25 (coluna separada).          |
| 14  | Limitações                          | Só conta imports estáticos e dinâmicos modeláveis; não conta uso por reflexão, strings, plugins; depende da resolução de imports; não distingue dependência de contrato de dependência de implementação. |
| 15  | Erros comuns                        | Somar testes ao Ca; contar importações repetidas; tratar Ca = 0 como “código morto”; comparar Ca de módulos de tamanhos diferentes sem contexto.                                                         |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py` (AST + imports dinâmicos verificáveis), validado por `verificacoes_independentes.py` (V7).                                                                                            |
| 17  | Status                              | **VALIDADO** (definição e recálculo independente).                                                                                                                                                       |
| 18  | O que se pode/não se pode concluir  | Pode-se concluir que um módulo é central e medir impacto potencial. Não se pode concluir que o módulo é bem projetado, que é código morto (Ca = 0) ou que o acoplamento é excessivo sem contexto.        |

### 5.1.1 Leitura do fan-in no SOLAR

- **Hub de exceção:** `solar_exception` (Ca 38) é a base das exceções do domínio; é esperado que muitas partes dependam dela. O risco é de contrato: mudar a assinatura da exceção afeta muitos pontos.
- **Contrato de regra:** `nucleus.rules.rule` (Ca 32) é a classe abstrata que todas as regras estendem. É um hub estrutural, não um módulo de negócio.
- **Infraestrutura de varredura:** `source_files` (Ca 17) é usado pelos scanners; é um hub de infraestrutura.
- **Ca = 0:** 70 módulos não são importados por nenhum módulo de produção. Isso inclui 59 inicializadores sem código, `nucleus.security.token` e módulos usados apenas por testes. **Não é prova de código morto.**

---

## 5.2 Fan-out (Ce)

| #   | Campo                               | Conteúdo                                                                                                                                                                                     |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Número de dependências de saída; acoplamento eferente                                                                                                                                        |
| 2   | Nome original                       | _Fan-out_; _efferent coupling_                                                                                                                                                               |
| 3   | Sigla                               | **Ce** — _efferent coupling_ (acoplamento eferente)                                                                                                                                          |
| 4   | Categoria                           | dependências e acoplamento                                                                                                                                                                   |
| 5   | O que é, em linguagem simples       | De quantos módulos este módulo depende. É como contar quantas estradas saem de uma cidade.                                                                                                   |
| 6   | O que mede exatamente               | Número de **módulos internos distintos** importados pelo módulo analisado. Bibliotecas externas e imports de teste não entram.                                                               |
| 7   | Por que é importante                | Ce alto significa que o módulo precisa conhecer muitos outros; isso aumenta o custo de teste, a superfície de mudança e a carga cognitiva.                                                   |
| 8   | Como é calculado                    | Para cada módulo de origem, coleta-se o conjunto de destinos internos distintos; `Ce(origem)` é o tamanho desse conjunto.                                                                    |
| 9   | Como interpretar                    | Alto: orquestração/composição ou excesso de responsabilidades. Baixo: módulo focado/folha. Contexto decide.                                                                                  |
| 10  | Cenário favorável                   | Um módulo de composição (`Kernel`) com Ce alto, mas centralizado e testado.                                                                                                                  |
| 11  | Cenário potencialmente desfavorável | Um módulo de domínio com Ce alto e muitas dependências de infraestrutura: difícil de testar e de evoluir.                                                                                    |
| 12  | Exemplo numérico                    | Se X importa A, B e C (uma vez cada), Ce(X) = 3. Se importa A duas vezes, continua 3. Se importa `flask`, não conta.                                                                         |
| 13  | Exemplo no SOLAR                    | `nucleus.rules.project_validator` tem Ce = 49; `nucleus.kernel` tem 16; `request_pipeline` tem 6. Há 107 módulos com Ce = 0. A distribuição tem mediana 3, média 3,03, P90 4 e máximo 49.    |
| 14  | Limitações                          | Não mede a qualidade da dependência; não vê imports dinâmicos não instrumentados; não distingue dependência de contrato de dependência de detalhe; não pondera o “peso” do módulo importado. |
| 15  | Erros comuns                        | Incluir bibliotecas externas no Ce; comparar Ce de um registro de regras com o de uma classe de domínio; concluir “complexo” apenas por Ce alto.                                             |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py` (grafo de imports); validação independente em V7 (3 de 4 módulos idênticos; o quarto explicado por 2 arestas dinâmicas).                                                  |
| 17  | Status                              | **VALIDADO** para o método declarado.                                                                                                                                                        |
| 18  | O que se pode/não se pode concluir  | Pode-se medir a amplitude das dependências de saída. Não se pode concluir que o módulo é mal projetado; `project_validator` e `kernel` têm Ce alto por papel arquitetural.                   |

### 5.2.1 Fan-out interno × externo

O relatório estrutural original publicou fan-out 18 para `kernel` e 51 para `project_validator`. A auditoria mostrou que esses valores só fecham quando se somam **duas dependências externas** a cada um:

- `kernel`: 16 internos + 2 externos (`flask`, `pathlib`) = 18;
- `project_validator`: 49 internos + 2 externos (`dataclasses`, `pathlib`) = 51.

Portanto, o número original **não é acoplamento interno**. Misturar bibliotecas externas com módulos do projeto muda o significado da métrica.

---

## 5.3 Instabilidade (I)

| #   | Campo                               | Conteúdo                                                                                                                                                               |
| --- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Instabilidade                                                                                                                                                          |
| 2   | Nome original                       | _Instability_                                                                                                                                                          |
| 3   | Sigla                               | **I** — _Instability_                                                                                                                                                  |
| 4   | Categoria                           | dependências e acoplamento                                                                                                                                             |
| 5   | O que é, em linguagem simples       | Uma proporção entre “quantas coisas eu uso” e “quantas coisas me usam”.                                                                                                |
| 6   | O que mede exatamente               | `I = Ce / (Ca + Ce)`, no intervalo de 0 a 1, quando `Ca + Ce > 0`.                                                                                                     |
| 7   | Por que é importante                | Ajuda a identificar módulos que dependem de muitos e são usados por poucos (frágeis a mudanças) e módulos estáveis que muitos usam.                                    |
| 8   | Como é calculado                    | Divide-se o fan-out pela soma de fan-in e fan-out. Não é uma média; é uma razão.                                                                                       |
| 9   | Como interpretar                    | `I = 0`: só recebe dependências (estável no sentido estrutural). `I = 1`: só tem dependências de saída. Valores intermediários: mistura. `Ca + Ce = 0`: indefinida.    |
| 10  | Cenário favorável                   | Contratos e exceções com I próximo de 0; pontos de composição com I próximo de 1, desde que centralizados.                                                             |
| 11  | Cenário potencialmente desfavorável | Módulo de detalhe com I próximo de 1 e poucos testes; ou módulo central com I próximo de 0 e contrato instável.                                                        |
| 12  | Exemplo numérico                    | `project_validator`: Ca = 2, Ce = 49 → `I = 49 / 51 = 0,961`. `solar_exception`: Ca = 38, Ce = 0 → `I = 0`. `token`: Ca = 0, Ce = 0 → indefinida.                      |
| 13  | Exemplo no SOLAR                    | 148 módulos têm I definida; 60 são indefinidos (59 inicializadores sem código + `token`). 10 têm I = 1; 20 têm I ≥ 0,8; 50 têm I ≤ 0,2.                                |
| 14  | Limitações                          | Não mede estabilidade operacional, disponibilidade ou taxa de falhas; depende de Ca/Ce; módulos sem conexões ficam sem valor; não pondera criticidade.                 |
| 15  | Erros comuns                        | Dizer que um módulo “instável” vai falhar; tratar `I = 0` como “perfeito”; calcular `0/0` como zero; comparar I de camadas diferentes sem separar arestas cruzadas.    |
| 16  | Ferramenta/procedimento no SOLAR    | Cálculo próprio sobre Ca/Ce validados; `resumo_metricas.json` → `coupling`.                                                                                            |
| 17  | Status                              | **VALIDADO** (aritmética sobre dados validados; indefinição tratada explicitamente).                                                                                   |
| 18  | O que se pode/não se pode concluir  | Pode-se descrever a direção estrutural das dependências. Não se pode concluir risco operacional, qualidade do contrato ou “arquitetura instável” em sentido coloquial. |

### 5.3.1 Instabilidade por camada

O I agregado de uma camada inclui arestas internas à própria camada. Para leitura arquitetural, o valor mais informativo é o **I entre camadas**:

| Camada          | Ce entre camadas | Ca entre camadas | I entre camadas |
| --------------- | ---------------- | ---------------- | --------------- |
| Bootstrap       | 5                | 0                | 1,000           |
| Nucleus         | 3                | 18               | 0,143           |
| Observatory     | 2                | 2                | 0,500           |
| Orbits          | 4                | 1                | 0,800           |
| Orbits/Database | 2                | 5                | 0,286           |
| Orbits/Planets  | 14               | 4                | 0,778           |

O Nucleus é a camada mais estável (I 0,143): muitos dependem dele e ele depende de poucas camadas externas. Os Planets são os mais instáveis (I 0,778), o que é coerente com módulos funcionais que consomem o núcleo e a persistência.

---

## 5.4 Acoplamento entre objetos (CBO)

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                                                                                                                                    |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Acoplamento entre objetos (ou entre classes)                                                                                                                                                                                                                                                                                                |
| 2   | Nome original                       | _Coupling Between Objects_                                                                                                                                                                                                                                                                                                                  |
| 3   | Sigla                               | **CBO** — _Coupling Between Objects_                                                                                                                                                                                                                                                                                                        |
| 4   | Categoria                           | dependências e acoplamento                                                                                                                                                                                                                                                                                                                  |
| 5   | O que é, em linguagem simples       | Quantas **outras classes** uma classe precisa conhecer para funcionar.                                                                                                                                                                                                                                                                      |
| 6   | O que mede exatamente               | Cardinalidade do conjunto de classes internas distintas referenciadas no corpo da classe: bases, anotações, instanciações, chamadas e acessos resolvíveis.                                                                                                                                                                                  |
| 7   | Por que é importante                | CBO alto sugere que a classe depende de muitos conceitos; isso pode indicar baixa coesão, dificuldade de teste e impacto de mudanças.                                                                                                                                                                                                       |
| 8   | Como é calculado                    | Tabela de símbolos por módulo (import → módulo ou símbolo); coleta de nomes e cadeias `a.b.c`; resolução para classes internas; nomes ambíguos vão para `cbo_internal_max`. CBO externo é uma heurística separada.                                                                                                                          |
| 9   | Como interpretar                    | Compare com a distribuição do projeto e com o papel da classe. Um composition root pode ter CBO alto legitimamente.                                                                                                                                                                                                                         |
| 10  | Cenário favorável                   | Classe de domínio com CBO baixo/médio e dependências de contrato.                                                                                                                                                                                                                                                                           |
| 11  | Cenário potencialmente desfavorável | Classe de domínio que referencia muitas classes de infraestrutura e detalhes.                                                                                                                                                                                                                                                               |
| 12  | Exemplo numérico                    | Se uma classe referencia `A`, `B` e `C`, CBO = 3. Se referencia `A` em cinco métodos, continua 3. Se referencia `Database.orm` (atributo de classe), não conta como classe.                                                                                                                                                                 |
| 13  | Exemplo no SOLAR                    | 136 classes; média 1,54; mediana 1; P90 3; máximo 15 (`Kernel`). `Kernel` referencia 15 classes (Broadcast, InMemoryBroadcast, Database, DriverSQLAlchemy, Environment, 3 exceções, ErrorHandler, RequestPipeline, SecurityHeaders, SecurityPolicy, Identity, LocalStorageDriver, Storage). `RequestPipeline` tem 6; `ProjectValidator`, 5. |
| 14  | Limitações                          | Aproximação por AST: não resolve tipos, fábricas, injeção por atributo, `getattr`, reflexão; CBO externo é heurístico; não é comparável a ferramentas tipadas; nomes ambíguos exigem faixa min/max.                                                                                                                                         |
| 15  | Erros comuns                        | Confundir CBO com fan-out (módulos ≠ classes); tratar o CBO de um composition root como defeito; comparar com valores de Java/C++ sem equivalência de método.                                                                                                                                                                               |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py` (AST); validação independente V6 nas 5 classes de maior CBO (conjuntos de alvos idênticos).                                                                                                                                                                                                                              |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (método aproximado; CBO absoluto/tipado pendente).                                                                                                                                                                                                                                                               |
| 18  | O que se pode/não se pode concluir  | Pode-se comparar classes dentro do projeto e identificar outliers. Não se pode afirmar o CBO absoluto como verdade universal nem concluir baixa qualidade só pelo número.                                                                                                                                                                   |

### 5.4.1 CBO × fan-out

Fan-out conta **módulos importados**; CBO conta **classes referenciadas**. Uma classe pode importar um único módulo que contém várias classes e ter CBO alto; outra pode importar vários módulos e referenciar poucas classes. São métricas diferentes, com denominadores diferentes.

### 5.4.2 CBO aproximado × CBO tipado

- **Aproximado (AST):** vê nomes e imports; não sabe o tipo real de um objeto recebido por parâmetro ou criado por fábrica.
- **Tipado:** resolve o tipo declarado/inferido; exige analisador de tipos e é mais preciso, mas ainda tem limites (reflexão, `getattr`, código dinâmico).

No SOLAR, apenas o aproximado foi executado. O tipado permanece **pendente**.

---

## 5.11 Grafos de dependência, SCCs e ciclos

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                |
| --- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Grafo de dependências; componentes fortemente conexos; ciclos                                                                                                                                                           |
| 2   | Nome original                       | _Dependency graph_; _Strongly Connected Components_; _cycles_                                                                                                                                                           |
| 3   | Sigla                               | **SCC** — _Strongly Connected Component_ (Componente Fortemente Conexo)                                                                                                                                                 |
| 4   | Categoria                           | dependências e acoplamento; ciclos                                                                                                                                                                                      |
| 5   | O que é, em linguagem simples       | Um mapa de cidades (nós) e estradas de mão única (arestas). Um ciclo é um caminho que volta ao ponto de partida.                                                                                                        |
| 6   | O que mede exatamente               | Nós = módulos; arestas = dependências; SCC = conjunto em que todos os nós se alcançam mutuamente; ciclo = SCC com mais de um nó ou auto-aresta.                                                                         |
| 7   | Por que é importante                | Ciclos dificultam inicialização, teste isolado e mudanças; SCCs mostram o grau de emaranhamento.                                                                                                                        |
| 8   | Como é calculado                    | Tarjan iterativo para SCCs; BFS/DFS para caminhos; contagem de arestas internas ao SCC.                                                                                                                                 |
| 9   | Como interpretar                    | Zero ciclos em um grafo completo é favorável. Um ciclo pode ser intencional; o contexto decide se é risco.                                                                                                              |
| 10  | Cenário favorável                   | Grafo acíclico, com direção clara e poucas arestas cruzadas.                                                                                                                                                            |
| 11  | Cenário potencialmente desfavorável | Ciclo entre módulos de camadas diferentes, com dependência temporal de inicialização.                                                                                                                                   |
| 12  | Exemplo numérico                    | A→B→C→A forma um SCC de tamanho 3. A→B→C, sem volta, não forma ciclo. Um grafo com 208 nós e 207 SCCs tem apenas um componente não trivial (de tamanho 2).                                                              |
| 13  | Exemplo no SOLAR                    | 208 nós, 306 arestas (304 estáticas + 2 dinâmicas); 0 ciclos estáticos; 1 ciclo dinâmico `nucleus.database.database ↔ orbits.database.models.user_model`; 207 SCCs; aresta tardia `kernel → orbits.routes` (linha 274). |
| 14  | Limitações                          | O grafo depende da regra de construção; imports dinâmicos não instrumentados podem faltar; um ciclo pode ser intencional; SCC não mede frequência de uso nem criticidade.                                               |
| 15  | Erros comuns                        | Declarar “zero ciclos” com grafo incompleto; tratar todo ciclo como defeito; ignorar dependência temporal; confundir ciclo de módulos com ciclo de chamadas em runtime.                                                 |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py` (Tarjan + imports dinâmicos) e `trace_imports.py` (evidência de runtime); `solar_ciclos_internos.json`.                                                                                              |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (estático + runtime em dois cenários; sem tracing de requisições).                                                                                                                           |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar que existe uma relação de dependência bidirecional e uma dependência temporal. Não se pode concluir defeito funcional, deadlock ou que o ciclo seja inevitável.                                         |

### 5.11.1 O ciclo `Database ↔ user_model`, passo a passo

**Fatos observados:**

1. `nucleus/database/database.py:36` define `MODELS_PACKAGE = "orbits.database.models"`.
2. `Database.init()` chama `sync()` (linha 85), que chama `_import_models()` (linha 138).
3. `_import_models()` chama `importlib.import_module` para o pacote (linha 157) e para cada módulo (linha 167).
4. `orbits/database/models/user_model.py:2` faz `from nucleus.database.database import Database`; na linha 5, `class Users(Database.orm)`.
5. No runtime, `Database` foi carregado no evento 226; `models` no 683 e `user_model` no 684; `Database.orm` já estava publicado no momento do import.
6. Sem `Database.init()`, o import de `user_model` falha com `AttributeError` (cenário C).

**Interpretação:** há um ciclo de dependência de módulos e uma dependência temporal do estado inicializado. O ciclo é intencional (o Model só pode ser importado após a publicação da ORM), mas exige ordem de inicialização. O risco é de erro pouco explícito se alguém importar o Model antes de `init()`.

**O que não se pode concluir:** que o sistema falha em operação normal (o `mount()` completou), que há deadlock ou que o ciclo deve ser removido sem avaliar o custo.

### 5.11.2 Importações tardias

A aresta `kernel → orbits.routes` está dentro de `Kernel.mount()` (linha 274). Ela é **tardia** para permitir que `Database.init()` publique a ORM antes de carregar os Planets. Importação tardia não é, por si, um problema: é uma técnica de controle de ordem. O problema é quando ela esconde uma dependência que ninguém documenta ou quando cria fragilidade de inicialização.

---

## 5.12 Fechamento do bloco de acoplamento

- **Ca** e **Ce** descrevem a posição de um módulo na rede.
- **I** resume a razão entre saída e entrada, com interpretação estrutural — não operacional.
- **CBO** olha para classes, não módulos, e é aproximado por AST.
- **Grafos/SCC** revelam ciclos; um grafo incompleto pode esconder o ciclo mais importante.
- Nenhuma dessas métricas, isolada, prova qualidade ou defeito.

**Próximo:** [Capítulo 5B](capitulo-05b-coesao-e-alcance.md) — coesão (LCOM) e alcançabilidade.
