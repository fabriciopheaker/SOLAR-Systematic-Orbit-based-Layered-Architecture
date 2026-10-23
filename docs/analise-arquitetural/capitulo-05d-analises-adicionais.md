# Capítulo 5D — Catálogo: análises complementares

> Última parte do catálogo. Cobre NOM, NOC, ramos/aninhamento, reprodutibilidade, tracing de runtime e o validador arquitetural.

---

## 5.13.1 Número de métodos (NOM)

| #   | Campo                               | Conteúdo                                                                                                                                                                                            |
| --- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Número de métodos por classe                                                                                                                                                                        |
| 2   | Nome original                       | _Number of Methods_                                                                                                                                                                                 |
| 3   | Sigla                               | **NOM** — _Number of Methods_                                                                                                                                                                       |
| 4   | Categoria                           | tamanho                                                                                                                                                                                             |
| 5   | O que é, em linguagem simples       | Quantos métodos uma classe declara.                                                                                                                                                                 |
| 6   | O que mede exatamente               | Contagem de métodos declarados na classe. Há duas variantes: **total** (inclui `__init__` e métodos especiais) e **excluindo especiais** (só métodos de instância/estáticos/classe “normais”).      |
| 7   | Por que é importante                | Muitos métodos podem indicar classe com muitas responsabilidades; poucos métodos podem indicar classe de dados ou wrapper.                                                                          |
| 8   | Como é calculado                    | Percorre-se a AST e contam-se `FunctionDef` e `AsyncFunctionDef` dentro da classe, separando métodos especiais (`__init__`, `__call__` etc.).                                                       |
| 9   | Como interpretar                    | Compare com a distribuição do projeto e com o papel da classe. NOM alto não é defeito automático.                                                                                                   |
| 10  | Cenário favorável                   | Classe coesa com NOM compatível com a responsabilidade.                                                                                                                                             |
| 11  | Cenário potencialmente desfavorável | NOM alto + LCOM4 > 1 + muitos atributos: possível classe “faz-tudo”.                                                                                                                                |
| 12  | Exemplo numérico                    | Classe com `__init__`, `run` e `validate`: NOM total = 3; excluindo especiais = 2.                                                                                                                  |
| 13  | Exemplo no SOLAR                    | `ErrorExposureScanner`: 14 métodos (excluindo especiais), 15 no total — o maior NOM. `ErrorLog` e `ProjectReport`: 12 e 11 no total. Há 28 classes com zero métodos de instância e 20 com apenas 1. |
| 14  | Limitações                          | Conta declarações, não complexidade; métodos herdados não entram; propriedades e métodos gerados dinamicamente podem não aparecer; variantes de contagem precisam ser declaradas.                   |
| 15  | Erros comuns                        | Comparar NOM total com NOM sem especiais; concluir “classe grande” só pelo NOM; ignorar que 48 classes têm 0 ou 1 método.                                                                           |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py`; `coesao_classes.csv`; auditoria do alerta NOM (1 alerta, confirmado).                                                                                                           |
| 17  | Status                              | **VALIDADO** (contagem reproduzida com variante declarada).                                                                                                                                         |
| 18  | O que se pode/não se pode concluir  | Pode-se medir a quantidade de métodos e localizar outliers. Não se pode concluir baixa coesão, complexidade ou qualidade apenas pelo NOM.                                                           |

### 5.13.2 O alerta de NOM

O relatório estrutural original apontou 14 métodos em `ErrorExposureScanner`. A auditoria reproduziu **14 excluindo especiais** e **15 no total**. O alerta é **confirmado**, desde que a variante seja declarada. Sem essa declaração, a diferença de 1 método parece divergência.

---

## 5.13.3 Número de classes (NOC)

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                                         |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Nome em português                   | Número de classes                                                                                                                                                                                                                                |
| 2   | Nome original                       | _Number of Classes_                                                                                                                                                                                                                              |
| 3   | Sigla                               | **NOC** — _Number of Classes_                                                                                                                                                                                                                    |
| 4   | Categoria                           | tamanho                                                                                                                                                                                                                                          |
| 5   | O que é, em linguagem simples       | Quantas classes existem em um módulo, camada ou projeto.                                                                                                                                                                                         |
| 6   | O que mede exatamente               | Contagem de definições de classe (`ClassDef`) em um escopo, com categorias: regulares, utilitárias (sem estado), abstratas/Protocol e de teste.                                                                                                  |
| 7   | Por que é importante                | Ajuda a dimensionar o projeto e a detectar módulos que concentram muitas classes.                                                                                                                                                                |
| 8   | Como é calculado                    | Percorre-se a AST; conta-se `ClassDef` por módulo; separa-se produção de testes; identifica-se herança direta de `ABC`/`Protocol`.                                                                                                               |
| 9   | Como interpretar                    | Compare a contagem com o número de módulos e com a camada. NOC alto em um único arquivo pode indicar baixa separação.                                                                                                                            |
| 10  | Cenário favorável                   | Classes distribuídas de forma coerente com os módulos; contagem reproduzível.                                                                                                                                                                    |
| 11  | Cenário potencialmente desfavorável | Muitas classes em um arquivo ou contagem que não fecha com a realidade do projeto.                                                                                                                                                               |
| 12  | Exemplo numérico                    | Um arquivo com 3 `class` tem NOC = 3. Se duas herdam de `ABC`, há 2 abstratas e 1 regular.                                                                                                                                                       |
| 13  | Exemplo no SOLAR                    | 136 classes de produção (124 regulares + 12 utilitárias) e 29 de teste. Nove herdam diretamente de `ABC`/`Protocol`. O relatório original publicou “127,6 classes ponderadas”, “124 regulares”, “12 utilitárias”, “29 de teste” e “0 abstratas”. |
| 14  | Limitações                          | “Classe ponderada” não é uma definição padrão; classes aninhadas e geradas dinamicamente podem escapar; a categoria “utilitária” depende de heurística; NOC não mede tamanho das classes.                                                        |
| 15  | Erros comuns                        | Aceitar “127,6 classes” sem fórmula; tratar “0 abstratas” como fato; somar classes de teste com produção; confundir NOC com número de filhos (herança).                                                                                          |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py`; auditoria do alerta NOC (`parcial`).                                                                                                                                                                                         |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (contagem total fecha; “weighted 127,6” e “abstract 0” não reproduzíveis).                                                                                                                                            |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar 136 classes de produção e 29 de teste. Não se pode reproduzir o valor ponderado nem aceitar “0 abstratas” — há 9 heranças diretas de `ABC`/`Protocol`.                                                                           |

### 5.13.4 O que não fecha no NOC original

| Item original                | Situação             | Evidência                                        |
| ---------------------------- | -------------------- | ------------------------------------------------ |
| “127,6 weighted classes”     | **não reproduzível** | nenhuma fórmula documentada; 127,6 não é inteiro |
| “124 regular” + “12 utility” | **confere**          | 124 + 12 = 136 = classes de produção             |
| “29 tests”                   | **confere**          | 29 classes de teste                              |
| “Abstract/Interface 0”       | **incorreto**        | 9 classes herdam diretamente de `ABC`/`Protocol` |

**Lição:** uma contagem que “fecha” em parte pode esconder um detalhe errado. A auditoria separa o que é reproduzível do que não é.

---

## 5.13.5 Ramos e aninhamento

| #   | Campo                               | Conteúdo                                                                                                                                                                                     |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Número de ramos; profundidade de aninhamento                                                                                                                                                 |
| 2   | Nome original                       | _Branches_; _nesting depth_                                                                                                                                                                  |
| 3   | Sigla                               | não há sigla consagrada                                                                                                                                                                      |
| 4   | Categoria                           | complexidade                                                                                                                                                                                 |
| 5   | O que é, em linguagem simples       | Quantos desvios de fluxo existem e quão fundo eles estão aninhados.                                                                                                                          |
| 6   | O que mede exatamente               | Ramos: quantidade de pontos de decisão. Aninhamento: maior profundidade de estruturas de controle dentro de outras.                                                                          |
| 7   | Por que é importante                | Aninhamento profundo é mais difícil de ler do que uma sequência de decisões planas, mesmo com a mesma CC.                                                                                    |
| 8   | Como é calculado                    | Percorre-se a AST contando estruturas de decisão e calculando a profundidade máxima de aninhamento por função/classe.                                                                        |
| 9   | Como interpretar                    | Compare com CC: em uma função sem `and`/`or`, espera-se `ramos = CC − 1`. Aninhamento alto com CC moderada indica legibilidade pior.                                                         |
| 10  | Cenário favorável                   | Ramos compatíveis com CC e aninhamento raso.                                                                                                                                                 |
| 11  | Cenário potencialmente desfavorável | Aninhamento profundo em função longa, com muitos caminhos.                                                                                                                                   |
| 12  | Exemplo numérico                    | `if` dentro de `for` dentro de `try`: 3 estruturas, aninhamento máximo 3 (ou 2, dependendo de `try` contar). CC = 1 + 3 = 4; ramos = 3 = CC − 1.                                             |
| 13  | Exemplo no SOLAR                    | 35 alertas de “Too Many Branches”. Em 22 de 35, os ramos publicados coincidem com `CC − 1`; em 13, não. O aninhamento publicado coincide com o recalculado em apenas **2 de 35**.            |
| 14  | Limitações                          | “Ramo” e “aninhamento” não têm definição única; `try/except`, `with`, `match` e operadores lógicos variam; a ferramenta original não está disponível; comparação depende da mesma convenção. |
| 15  | Erros comuns                        | Tratar ramos como CC; aceitar aninhamento publicado sem recálculo; comparar contagens de ferramentas diferentes.                                                                             |
| 16  | Ferramenta/procedimento no SOLAR    | Recálculo próprio por AST; auditoria dos 35 alertas (`revisar_relatorio.py`).                                                                                                                |
| 17  | Status                              | **PARCIAL** (ramos parcialmente reproduzíveis; aninhamento quase não reproduzível).                                                                                                          |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar que a contagem de ramos é compatível com CC em 22 de 35 casos. Não se pode usar o aninhamento publicado como evidência: 33 de 35 valores não batem.                          |

### 5.13.6 Por que o aninhamento diverge tanto

O valor publicado parece contar **estruturas totais** ou usar outra noção de profundidade. O recálculo encontra profundidades menores na maioria dos casos. Sem a ferramenta original, não é possível saber se o erro está na definição, na implementação ou na extração. O correto é registrar **não reproduzível** e não usar o número como prova.

---

## 5.13.7 Alertas de arquivo longo e LOC

| Alerta       | Quantidade | Veredicto                                                                                | Leitura                                                                                      |
| ------------ | ---------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Long File    | 4          | 2 confirmados + 2 fora de escopo                                                         | os fora de escopo são arquivos de teste; o alerta não distingue produção de teste            |
| High LOC     | 5          | 5 parciais                                                                               | o total do módulo não fecha com o detalhe publicado                                          |
| High Fan-in  | 7          | 4 falsos positivos, 2 confirmados, 1 parcial                                             | falsos positivos por contar bibliotecas externas (`pathlib`, `dataclasses`, `ast`, `pytest`) |
| High Fan-out | 2          | 2 confirmados                                                                            | `kernel` 18 e `project_validator` 51, mas com 2 externos cada                                |
| High NOM     | 1          | confirmado                                                                               | 14 métodos (sem especiais)                                                                   |
| High NOC     | 1          | parcial                                                                                  | contagem total confere; weighted e abstract não                                              |
| **Total**    | **60**     | **7 confirmados, 7 falsos positivos, 43 parciais, 1 não reproduzível, 2 fora de escopo** |                                                                                              |

**Leitura geral:** a maioria dos alertas é **parcial**: o valor principal às vezes confere, mas o detalhamento publicado não fecha. Isso não invalida o alerta; invalida o detalhe como evidência.

### 5.13.7.1 Ficha do alerta “Long File”

| #   | Campo                               | Conteúdo                                                                                                                                               |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Nome em português                   | Arquivo longo                                                                                                                                          |
| 2   | Nome original                       | _Long File_                                                                                                                                            |
| 3   | Sigla                               | não há                                                                                                                                                 |
| 4   | Categoria                           | tamanho                                                                                                                                                |
| 5   | O que é, em linguagem simples       | Um arquivo com muitas linhas, que exige mais tempo de leitura e navegação.                                                                             |
| 6   | O que mede exatamente               | Número de linhas do arquivo (LOC), comparado a um limiar definido pela ferramenta original.                                                            |
| 7   | Por que é importante                | Arquivos longos concentram responsabilidades e dificultam localizar código.                                                                            |
| 8   | Como é calculado                    | Contagem de linhas físicas do arquivo; o limiar não é documentado no relatório original.                                                               |
| 9   | Como interpretar                    | Compare com o papel do arquivo e com o LOC/SLOC. Arquivos de composição e listas de regras podem ser longos legitimamente.                             |
| 10  | Cenário favorável                   | Arquivo longo com uma única responsabilidade clara e baixa complexidade por função.                                                                    |
| 11  | Cenário potencialmente desfavorável | Arquivo longo com muitas classes/funções e responsabilidades misturadas.                                                                               |
| 12  | Exemplo numérico                    | `project_validator` tem LOC 423, SLOC 269 e LLOC 107; é um registro de regras, não um módulo de negócio.                                               |
| 13  | Exemplo no SOLAR                    | 4 alertas: 2 confirmados em produção e 2 fora de escopo (arquivos de teste).                                                                           |
| 14  | Limitações                          | O limiar original não é documentado; LOC é sensível a estilo; o alerta não separa produção de teste; arquivo longo não é sinônimo de arquivo complexo. |
| 15  | Erros comuns                        | Tratar “Long File” como “código ruim”; ignorar que 2 alertas são de teste; comparar LOC com SLOC.                                                      |
| 16  | Ferramenta/procedimento no SOLAR    | Auditoria do relatório original (`revisar_relatorio.py`); Radon `raw`.                                                                                 |
| 17  | Status                              | **PARCIAL** (2 confirmados; 2 fora de escopo; limiar não reproduzível).                                                                                |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar que dois arquivos de produção são longos. Não se pode concluir baixa qualidade nem que o limiar seja universal.                        |

---

## 5.13.8 Reprodutibilidade e determinismo

| #   | Campo                               | Conteúdo                                                                                                                                             |
| --- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Reprodutibilidade e determinismo                                                                                                                     |
| 2   | Nome original                       | _Reproducibility_; _determinism_                                                                                                                     |
| 3   | Sigla                               | não se aplica                                                                                                                                        |
| 4   | Categoria                           | análises complementares                                                                                                                              |
| 5   | O que é, em linguagem simples       | Duas execuções do mesmo método, sobre o mesmo código, produzem os mesmos resultados?                                                                 |
| 6   | O que mede exatamente               | Igualdade de saídas (CSV/JSON) entre execuções independentes, após normalização de campos voláteis (timestamp, caminho absoluto).                    |
| 7   | Por que é importante                | Sem reprodutibilidade, qualquer conclusão pode ser artefato de ordenação, ambiente ou aleatoriedade.                                                 |
| 8   | Como é calculado                    | Executa-se duas vezes; normaliza-se o que muda legitimamente; compara-se por hash e por conteúdo.                                                    |
| 9   | Como interpretar                    | Hashing idêntico: reprodutível. Diferença: investigar ordenação, dicionários, timestamps, caminhos.                                                  |
| 10  | Cenário favorável                   | Todos os artefatos com hash idêntico entre execuções.                                                                                                |
| 11  | Cenário potencialmente desfavorável | Resultados que mudam de ordem ou de valor sem mudança de código.                                                                                     |
| 12  | Exemplo numérico                    | Duas execuções geram 306 arestas, 553 funções, CC total 1.278 e hashes iguais.                                                                       |
| 13  | Exemplo no SOLAR                    | `solar_metrics.py` foi ajustado para ordenar empates de forma determinística; o tracing normaliza timestamps e caminhos; os hashes coincidiram.      |
| 14  | Limitações                          | Determinismo não garante corretude; o ambiente (versões de Radon/flake8/Python) precisa ser registrado; normalização pode mascarar diferenças reais. |
| 15  | Erros comuns                        | Confundir reprodutibilidade com validação; comparar arquivos com timestamps; rodar em ambientes diferentes sem registrar versões.                    |
| 16  | Ferramenta/procedimento no SOLAR    | Execuções repetidas + `hashlib`; `verificacoes_independentes.py`; relatório de runtime.                                                              |
| 17  | Status                              | **VALIDADO** (hashes idênticos após normalização declarada).                                                                                         |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar que o método é determinístico no ambiente registrado. Não se pode afirmar que os resultados são corretos só por serem estáveis.      |

---

## 5.13.9 Tracing de importações em runtime

| #   | Campo                               | Conteúdo                                                                                                                                                                                               |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Nome em português                   | Rastreamento de importações em tempo de execução                                                                                                                                                       |
| 2   | Nome original                       | _Runtime import tracing_                                                                                                                                                                               |
| 3   | Sigla                               | não se aplica                                                                                                                                                                                          |
| 4   | Categoria                           | alcance e utilização; análises complementares                                                                                                                                                          |
| 5   | O que é, em linguagem simples       | Executar o sistema e registrar, de verdade, quais módulos foram carregados.                                                                                                                            |
| 6   | O que mede exatamente               | Módulos em `sys.modules` após a execução; importações observadas por auditoria (`sys.addaudithook`); importações dinâmicas capturadas por wrapper de `importlib.import_module`.                        |
| 7   | Por que é importante                | Confirma ou refuta conclusões estáticas sobre uso, ciclos e alcançabilidade.                                                                                                                           |
| 8   | Como é calculado                    | Três cenários: **A** verificador arquitetural; **B** bootstrap do `Kernel`; **C** importação isolada de `user_model`. Compara-se o conjunto observado com o grafo estático.                            |
| 9   | Como interpretar                    | Módulo observado: existe uso naquele cenário. Módulo não observado: candidato, não prova.                                                                                                              |
| 10  | Cenário favorável                   | Todos os módulos alcançáveis observados; nenhum ciclo inesperado.                                                                                                                                      |
| 11  | Cenário potencialmente desfavorável | Módulos de segurança/regra nunca observados; ciclo dinâmico não modelado.                                                                                                                              |
| 12  | Exemplo numérico                    | Cenário A: 85 módulos SOLAR, saída 0, 1 auditoria correta; B: 172 módulos, `mount()` concluído, 3 regras de URL e 5 blueprints; C: 13 módulos e `AttributeError`.                                      |
| 13  | Exemplo no SOLAR                    | União: 175 módulos SOLAR (133 com código + 42 pais implícitos); 14 ausentes em todos os cenários (625 SLOC); `observatory.log` refutado como não alcançável; ciclo `Database ↔ user_model` confirmado. |
| 14  | Limitações                          | Três cenários não cobrem rotas, middlewares e jobs; imports por reflexão podem escapar; o auditor não vê código em C; o ambiente de execução influencia o conjunto carregado.                          |
| 15  | Erros comuns                        | Chamar ausência de “código morto”; comparar cenários diferentes como se fossem o mesmo; ignorar pacotes-pai; tratar `sys.modules` como lista de uso.                                                   |
| 16  | Ferramenta/procedimento no SOLAR    | `trace_imports.py`; `imports_runtime_*.json`; `comparacao_alcancabilidade.json`.                                                                                                                       |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (3 cenários; sem tracing de requisições completas).                                                                                                                         |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar o que foi carregado nos cenários. Não se pode afirmar cobertura total, inexistência de uso ou ausência de defeito.                                                                     |

### 5.13.10 Os três cenários em detalhe

| Cenário                | O que executa                              | Módulos SOLAR | Resultado                                                                             | O que prova                                                          |
| ---------------------- | ------------------------------------------ | ------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **A — verificador**    | `observatory.solar` verifica o projeto     | 85            | saída 0; 1 auditoria; 3 externos, 24 stdlib, 10 builtin                               | o caminho do verificador funciona e não carrega módulos de rota      |
| **B — bootstrap**      | `Kernel.mount()`                           | 172           | `mount()` conclui; 3 regras de URL; 5 blueprints; 16 externos, 136 stdlib, 21 builtin | a composição carrega a maior parte do sistema; ciclo dinâmico ocorre |
| **C — modelo isolado** | importa `user_model` sem `Database.init()` | 13            | `AttributeError`                                                                      | o modelo depende do estado inicializado; ciclo é real                |

**O que os três não provam:** que uma rota HTTP funciona, que um middleware é exercitado, que um upload é processado. Para isso seria preciso um cenário com requisições.

---

## 5.13.11 `ProjectValidator` e as 29 regras

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                     |
| --- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Validador arquitetural do projeto                                                                                                                                                                                            |
| 2   | Nome original                       | _Project Validator_                                                                                                                                                                                                          |
| 3   | Sigla                               | não se aplica                                                                                                                                                                                                                |
| 4   | Categoria                           | análises complementares                                                                                                                                                                                                      |
| 5   | O que é, em linguagem simples       | Um programa que lê o código e verifica se as regras arquiteturais do SOLAR são respeitadas.                                                                                                                                  |
| 6   | O que mede exatamente               | Executa 17 verificações e 29 regras sobre todos os arquivos `.py`; produz relatório com violações.                                                                                                                           |
| 7   | Por que é importante                | Fornece uma checagem automatizada de conformidade arquitetural, complementando métricas.                                                                                                                                     |
| 8   | Como é calculado                    | `ProjectValidator` instancia as regras, os scanners e o relatório; cada regra analisa a AST e emite violações.                                                                                                               |
| 9   | Como interpretar                    | `correct` com 0 violações: nenhuma regra disparou. Isso não significa que o código esteja perfeito; significa que as regras implementadas não encontraram violação.                                                          |
| 10  | Cenário favorável                   | Execução `correct`, 0 violações, sem erro de análise.                                                                                                                                                                        |
| 11  | Cenário potencialmente desfavorável | Violações, exceções ou regras não registradas.                                                                                                                                                                               |
| 12  | Exemplo numérico                    | 17 verificações, 29 regras, 0 violações, resultado `correct`.                                                                                                                                                                |
| 13  | Exemplo no SOLAR                    | Execução registrada em `verificador_stdout.txt`; a regra `ControllerAndUseCaseMustUseNamedContracts` implementa `SOLAR-ROF-003`, tem teste unitário, mas **não está entre as 29 regras instanciadas no `ProjectValidator`**. |
| 14  | Limitações                          | Cobre apenas as regras implementadas; não mede eficácia das regras; não testa comportamento; uma regra não registrada não é executada; o analisador pode ter falsos positivos/negativos.                                     |
| 15  | Erros comuns                        | Concluir “arquitetura 100% conforme” com 0 violações; ignorar regras não registradas; confundir validação estática com teste funcional.                                                                                      |
| 16  | Ferramenta/procedimento no SOLAR    | `python -m observatory.solar`; relatório em `verificador_stdout.txt`.                                                                                                                                                        |
| 17  | Status                              | **INFORMATIVO** (não é métrica quantitativa; é verificação de conformidade).                                                                                                                                                 |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar que as 29 regras registradas não encontraram violação. Não se pode afirmar conformidade arquitetural completa nem que todas as regras do SOLAR estão ativas.                                                 |

### 5.13.12 A regra que não está registrada

`ControllerAndUseCaseMustUseNamedContracts` declara `SOLAR-ROF-003` e é a única classe com esse código. Ela não aparece entre as 29 regras instanciadas em `project_validator.py`. Consequências:

- o validador não a executa;
- “0 violações” não cobre essa regra;
- a conformidade declarada é **parcial por construção**;
- isso não significa que a regra não tenha implementação: ela tem classe e teste
  unitário, e não é uma regra de persistência.

Esse é um exemplo de limite que não aparece no número: o resultado “0 violações” é verdadeiro para o conjunto executado, mas o conjunto não é o universo de regras.

---

## 5.13.13 Resumo das análises complementares

| Análise            | O que acrescenta                 | Status                 |
| ------------------ | -------------------------------- | ---------------------- |
| NOM                | dimensão “quantidade de métodos” | validado               |
| NOC                | dimensionamento de classes       | validado com ressalvas |
| Ramos/aninhamento  | legibilidade além da CC          | parcial                |
| LOC/Long File      | tamanho e alertas                | validado/parcial       |
| Reprodutibilidade  | confiança no método              | validado               |
| Runtime            | confirmação/refutação estática   | validado com ressalvas |
| `ProjectValidator` | conformidade de regras           | informativo            |

---

## 5.14 Matriz de cenários: favorável, desfavorável e inconclusivo

As fichas das seções anteriores trazem os cenários favorável e desfavorável. Esta matriz acrescenta o **inconclusivo** — a situação em que o número, sozinho, não permite decidir — e o **não aplicável**.

| Métrica               | Favorável                                           | Desfavorável                                        | Inconclusivo                                      | Não aplicável                   |
| --------------------- | --------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------- | ------------------------------- |
| **Ca**                | contrato estável com Ca alto                        | detalhe de implementação com Ca alto                | Ca = 0 (folha, init ou não usado)                 | —                               |
| **Ce**                | composição centralizada com Ce alto                 | domínio com Ce alto e dependência de infraestrutura | Ce = 0 sem contexto de uso                        | —                               |
| **I**                 | contrato com I ≈ 0; composição com I ≈ 1            | detalhe com I ≈ 1 e sem testes                      | valor intermediário sem papel definido            | `Ca + Ce = 0`                   |
| **CBO**               | domínio com CBO baixo/médio                         | domínio referenciando muita infraestrutura          | outlier sem leitura do papel                      | —                               |
| **LCOM1**             | baixo com métodos conectados por estado             | alto com LCOM4 > 1 e muitos atributos               | alto por número de métodos, com LCOM4 = 1         | classe sem estado de instância  |
| **LCOM4**             | 1 componente                                        | > 1 em classe de domínio                            | > 1 em composition root/fachada                   | classe sem métodos suficientes  |
| **LCOM\***            | próximo de 0                                        | próximo de 1 com estado real                        | valor médio sem contexto                          | classe sem estado               |
| **TCC**               | alto (métodos compartilham atributos)               | baixo com estado fragmentado                        | baixo com métodos conectados por chamada          | classe sem atributos            |
| **CC**                | mediana baixa; sem ranks altos                      | outlier com muitas decisões e poucos testes         | CC baixo com função longa e difícil de ler        | —                               |
| **Cognitiva**         | mediana baixa; nada acima de 15                     | outlier acima de 15 com CC alta                     | valor próximo do limiar sem dados de teste        | —                               |
| **LOC/SLOC/LLOC**     | dentro da faixa típica                              | muito acima do P90 com muitas responsabilidades     | arquivo longo e linear, de composição             | —                               |
| **Long File**         | longo com uma responsabilidade e baixa complexidade | longo com muitas classes/funções                    | limiar não documentado                            | arquivo de teste fora do escopo |
| **NOM**               | compatível com a responsabilidade                   | alto + LCOM4 > 1 + muitos atributos                 | alto em classe funcional                          | classe sem métodos              |
| **NOC**               | distribuído de forma coerente                       | muitas classes em um arquivo                        | contagem ponderada não reproduzível               | —                               |
| **Halstead**          | volume calculado para a maioria                     | volume alto com complexidade alta                   | zero por limitação do visitor                     | —                               |
| **MI**                | alto com volume real                                | baixo com volume/complexidade altos                 | 100 por saturação; outlier sensível a comentários | `V = 0` ou `LLOC = 0`           |
| **Ciclos**            | 0 ciclos no grafo completo                          | ciclo entre camadas com ordem frágil                | ciclo intencional sem falha observada             | —                               |
| **Alcançabilidade**   | todos os módulos com código alcançáveis             | módulo crítico inalcançável                         | não observado em runtime                          | pacote-pai sem código           |
| **Ramos/aninhamento** | ramos = CC − 1 e aninhamento raso                   | aninhamento profundo com CC alta                    | contagem publicada não reproduzível               | —                               |
| **Reprodutibilidade** | hashes idênticos                                    | resultados mudam sem mudança de código              | —                                                 | —                               |
| **Runtime**           | todos os alcançáveis observados                     | módulo crítico nunca observado                      | cenários não cobrem o fluxo                       | —                               |
| **Validador**         | `correct` nas regras executadas                     | violação                                            | regra sem scanner                                 | regra não registrada            |

**Regra de uso:** a coluna “inconclusivo” não é um fracasso da análise; é o reconhecimento de que o dado disponível não basta. A coluna “não aplicável” protege contra falsos positivos por construção.

**Fim do catálogo.**

**Próximo:** [Capítulo 6](capitulo-06-glossario.md) — glossário de todos os termos e siglas.
