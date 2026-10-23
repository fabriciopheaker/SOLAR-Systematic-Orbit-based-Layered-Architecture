# Capítulo 7 — Ferramentas utilizadas

> **Pergunta deste capítulo:** com o que cada número foi produzido, e o que essa ferramenta não vê?

---

## 7.1 Inventário

| Ferramenta                      | Versão           | Papel                               | Saída principal                   |
| ------------------------------- | ---------------- | ----------------------------------- | --------------------------------- |
| Python                          | 3.14.7 (CPython) | execução, AST, runtime              | base de tudo                      |
| Radon                           | 6.0.1            | CC, Halstead, MI, LOC/SLOC/LLOC     | JSON/CSV de métricas              |
| flake8                          | 7.4.1            | lint e hospedagem do plugin         | saída textual                     |
| flake8-cognitive-complexity     | 0.1.0            | complexidade cognitiva “sonar-like” | CSV de funções                    |
| `ast` (stdlib)                  | 3.14.7           | parsers próprios                    | grafo, CBO, LCOM, alcançabilidade |
| `sys.addaudithook` (stdlib)     | 3.14.7           | auditoria de importações            | eventos de import                 |
| `importlib` (stdlib)            | 3.14.7           | captura de imports dinâmicos        | alvos dinâmicos                   |
| `ProjectValidator` (projeto)    | —                | conformidade arquitetural           | relatório `correct`/violações     |
| `solar_metrics.py`              | —                | orquestração das métricas           | CSVs/JSONs                        |
| `verificacoes_independentes.py` | —                | validação V1–V9                     | relatório de conferência          |
| `trace_imports.py`              | —                | tracing de runtime                  | JSONs de cenários                 |

**Versões importam.** Radon 6.0.1 e flake8 7.4.1 produzem resultados que podem diferir de outras versões. O ambiente está registrado para permitir reprodução.

---

## 7.2 Radon

| Campo                          | Conteúdo                                                                                                                                                   |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Para que serve**             | Calcular CC, Halstead, MI e métricas brutas de linhas.                                                                                                     |
| **O que produz**               | `cc` (blocos e funções), `hal` (operadores/operandos/volume), `mi` (índice), `raw` (LOC/SLOC/LLOC/comentários).                                            |
| **Onde entra**                 | Etapas 2 e 3 (acoplamento, complexidade, tamanho, MI).                                                                                                     |
| **Pontos fortes**              | Ferramenta madura, amplamente usada, reproduce fórmulas conhecidas; API oficial permite recomputar MI.                                                     |
| **Limitações**                 | O visitor de Halstead não visita `Call` e `Subscript`; MI satura com volume zero; ranks são convenção; CC não vê complexidade de dados; não resolve tipos. |
| **Validação**                  | MI recomputado pela API oficial: 0 divergências em 269 módulos; CC, raw e Halstead conferidos em amostra.                                                  |
| **O que não se pode concluir** | Que um rank A significa código perfeito; que Halstead zero significa função trivial; que MI 100 significa manutenibilidade ótima.                          |

### 7.2.1 Radon `cc`

Conta blocos e funções, com rank A–F. No SOLAR, 553 funções de produção, soma 1.278, máximo 10. A validação independente recalculou a soma e o máximo.

### 7.2.2 Radon `hal`

Conta operadores e operandos. A limitação do visitor é a causa de 52,62% das funções de produção terem `n1 = n2 = 0`. O volume total não deve ser lido como “tamanho real” sem essa ressalva.

### 7.2.3 Radon `mi`

Reproduz a fórmula com termo de comentários. A validação oficial confirmou 0 divergências, mas a **validade** do MI como discriminador é limitada pela saturação.

### 7.2.4 Radon `raw`

Fornece LOC, SLOC, LLOC, comentários, multilinhas e brancos. É a base do tamanho e do MI. O detalhe por função não reconstrói o total do módulo (código fora de funções).

---

## 7.3 flake8 + `flake8-cognitive-complexity`

| Campo                          | Conteúdo                                                                                                                         |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **Para que serve**             | Calcular complexidade cognitiva por função.                                                                                      |
| **O que produz**               | Valor por função; CSV com módulo, camada, linha e qualname.                                                                      |
| **Onde entra**                 | Etapa 3 (complexidade).                                                                                                          |
| **Pontos fortes**              | Implementa o modelo “sonar-like” com penalidade de aninhamento; simples de executar; resultado determinístico.                   |
| **Limitações**                 | **Não é o Sonar oficial**; os incrementos podem diferir; só reporta funções com valor > 0; não mede complexidade de domínio.     |
| **Validação**                  | Soma 794 e máximo 18 conferidos por recálculo independente; distribuição por camada consistente.                                 |
| **O que não se pode concluir** | Equivalência numérica com o Sonar; que 15 seja um limite universal; que funções ausentes do CSV tenham complexidade zero “real”. |

**Por que “sonar-like”:** o plugin segue o modelo conceitual do Sonar (estruturas + aninhamento + sequências lógicas), mas é uma implementação independente. Comparar valores com o Sonar oficial exigiria rodar o Sonar.

---

## 7.4 Biblioteca padrão do Python

### 7.4.1 `ast`

| Campo              | Conteúdo                                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Para que serve** | Ler a estrutura do código sem executá-lo.                                                                                                         |
| **O que produz**   | Nós de módulo, classe, função, import, chamada, atributo etc.                                                                                     |
| **Usos no SOLAR**  | Grafo de imports, CBO, LCOM, NOM, NOC, ramos, aninhamento, alcançabilidade estática.                                                              |
| **Limitações**     | Não resolve tipos; não executa; imports dinâmicos não aparecem como arestas; reflexão e `getattr` escapam; a interpretação depende do analisador. |
| **Validação**      | Comparação com implementações independentes para CC, LCOM, CBO e acoplamento.                                                                     |

### 7.4.2 `sys.addaudithook`

| Campo              | Conteúdo                                                                                                               |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **Para que serve** | Observar eventos de importação em runtime.                                                                             |
| **O que produz**   | Sequência de eventos `import` com módulo, caminho e linha.                                                             |
| **Usos no SOLAR**  | Confirmar a ordem de carga e o ciclo `Database ↔ user_model`.                                                          |
| **Limitações**     | Não vê código em C; pode não capturar todos os mecanismos; adiciona overhead; o conjunto observado depende do cenário. |
| **Validação**      | Comparação com `sys.modules` e com o wrapper de `importlib`.                                                           |

### 7.4.3 `sys.modules` e `importlib`

| Campo              | Conteúdo                                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------------------------------- |
| **Para que serve** | Saber o que foi carregado e capturar imports dinâmicos.                                                             |
| **O que produz**   | Conjunto de módulos carregados; alvos de `import_module`.                                                           |
| **Usos no SOLAR**  | União de 175 módulos SOLAR; 14 ausentes; 2 alvos dinâmicos modelados.                                               |
| **Limitações**     | `sys.modules` não é lista de “uso”; imports implícitos de pacotes-pai aparecem; imports por reflexão podem escapar. |
| **Validação**      | Três cenários independentes; normalização de timestamps/caminhos.                                                   |

---

## 7.5 Algoritmos implementados no projeto

| Algoritmo                         | Para que serve                                 | Validação                                            | Limitação                                   |
| --------------------------------- | ---------------------------------------------- | ---------------------------------------------------- | ------------------------------------------- |
| **Tarjan**                        | Encontrar SCCs e ciclos                        | 207 SCCs; 0 ciclos estáticos; 1 ciclo dinâmico       | depende do grafo construído                 |
| **BFS**                           | Alcançabilidade a partir dos pontos de entrada | 134/208 estático; comparação com runtime             | depende dos pontos de entrada e das arestas |
| **LCOM1/LCOM4/LCOM\*/TCC**        | Coesão                                         | 39 classes conferidas por implementação independente | não se aplica a classes sem estado          |
| **CBO por AST**                   | Acoplamento entre classes                      | top 5 conferido                                      | aproximação; não resolve tipos              |
| **Contagem de ramos/aninhamento** | Legibilidade                                   | 35 alertas revisados                                 | definição não é universal                   |

**Por que implementar em vez de usar ferramenta pronta:** o projeto precisava de métricas integradas ao grafo e ao modelo SOLAR (camadas, módulos, classes). Ferramentas prontas não forneciam essa combinação. O custo é que a implementação precisa ser validada — e foi.

---

## 7.6 `ProjectValidator`

| Campo                          | Conteúdo                                                                                                                                                                    |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Para que serve**             | Verificar conformidade com as regras arquiteturais do SOLAR.                                                                                                                |
| **O que produz**               | Relatório com 17 verificações, 29 regras e 0 violações (`correct`).                                                                                                         |
| **Onde entra**                 | Análise complementar; cenário A do runtime.                                                                                                                                 |
| **Pontos fortes**              | Verifica regras específicas do estilo; executa sobre todos os `.py`; integra-se ao fluxo do projeto.                                                                        |
| **Limitações**                 | Só verifica as regras implementadas; `SOLAR-ROF-003` não tem scanner no `ProjectValidator` (mas tem teste unitário); não testa comportamento; não mede eficácia das regras. |
| **Validação**                  | Execução registrada; saída `correct`; auditoria das regras.                                                                                                                 |
| **O que não se pode concluir** | Que a arquitetura está 100% conforme; que todas as regras do SOLAR estão ativas.                                                                                            |

---

## 7.7 Scripts de análise

| Script                          | Entrada                    | Saída                               | Reprodutível?                  |
| ------------------------------- | -------------------------- | ----------------------------------- | ------------------------------ |
| `solar_metrics.py`              | código-fonte               | CSVs/JSONs de métricas              | sim (ordenação determinística) |
| `revisar_relatorio.py`          | `relatorio_estrutural.csv` | `alertas_estruturais_revisados.csv` | sim                            |
| `verificacoes_independentes.py` | CSVs/JSONs + código        | relatório V1–V9                     | sim                            |
| `trace_imports.py`              | código + cenários          | JSONs de runtime                    | sim após normalização          |

**Regra de ouro:** um script de análise não deve alterar o código de produção. Todos os scripts vivem em `observatory/audits/` e escrevem apenas nos artefatos da etapa correspondente.

---

## 7.8 Matriz ferramenta × métrica × status

| Métrica           | Ferramenta/método     | Status                 |
| ----------------- | --------------------- | ---------------------- |
| Ca, Ce, I         | `ast` + grafo próprio | validado               |
| CBO               | `ast` aproximado      | validado com ressalvas |
| LCOM1/4/\*/TCC    | `ast` próprio         | validado com ressalvas |
| CC                | Radon `cc`            | validado               |
| Cognitiva         | flake8 + plugin       | validado com ressalvas |
| Tamanho           | Radon `raw`           | validado               |
| Halstead          | Radon `hal`           | validado com ressalvas |
| MI                | Radon `mi`            | validado com ressalvas |
| SCC/ciclos        | Tarjan próprio        | validado com ressalvas |
| Alcançabilidade   | BFS próprio + runtime | validado com ressalvas |
| NOM/NOC           | `ast` próprio         | validado/parcial       |
| Ramos/aninhamento | `ast` próprio         | parcial                |
| Conformidade      | `ProjectValidator`    | informativo            |

---

## 7.9 O que **não** foi usado

| Ferramenta/técnica                                     | Por que não                                                   | Consequência                            |
| ------------------------------------------------------ | ------------------------------------------------------------- | --------------------------------------- |
| SonarQube/SonarCloud oficial                           | exigiria instalação e configuração; o plugin cobre o conceito | complexidade cognitiva não é oficial    |
| CBO com resolução de tipos (`mypy`, `pyright`, `jedi`) | custo e escopo                                                | CBO é aproximado                        |
| Halstead com visitor completo                          | exige implementação própria                                   | 52,62% das funções de produção com zero |
| Testes de mutação                                      | fora do escopo                                                | não mede eficácia dos testes            |
| Análise de cobertura de testes                         | não executada nesta rodada                                    | não se sabe a cobertura real            |
| Benchmarks de desempenho                               | fora do escopo                                                | não há dados de tempo/memória           |
| Análise histórica (git)                                | uma única fotografia                                          | não há tendência                        |

**Declarar o que não foi usado é parte da validade.** Um relatório que só lista ferramentas usadas esconde lacunas.

---

## 7.10 Ambiente de execução

| Item                        | Valor                          |
| --------------------------- | ------------------------------ |
| Sistema operacional         | Windows 11                     |
| Python                      | 3.14.7 CPython                 |
| Gerenciador                 | `py` (não há `python` no PATH) |
| Flask                       | 3.1.3                          |
| SQLAlchemy                  | 2.1.1                          |
| Alembic                     | 1.20.0                         |
| Radon                       | 6.0.1                          |
| flake8                      | 7.4.1                          |
| flake8-cognitive-complexity | 0.1.0                          |

**Reprodutibilidade:** os mesmos comandos, no mesmo ambiente, produzem os mesmos artefatos. O `pytest.ini` e o `requirements.txt` registram parte do ambiente; as versões das ferramentas de análise estão neste capítulo.

---

## 7.11 Limites gerais das ferramentas

1. **Toda ferramenta vê uma representação, não o sistema.** AST não é execução; runtime não é todos os fluxos.
2. **Toda ferramenta tem um viés de definição.** “Ramo”, “operador”, “comentário” variam.
3. **Toda ferramenta tem um custo.** Rodar Sonar, tipagem e mutação exigiria tempo e configuração.
4. **Nenhuma ferramenta substitui leitura de código.** Os outliers precisam de inspeção humana.
5. **Nenhuma ferramenta prova qualidade.** Ela mede propriedades; a conclusão é interpretativa.

---

## 7.12 Resumo do capítulo

- Radon fornece CC, Halstead, MI e tamanho; é oficial, mas tem limitações de visitor e saturação.
- flake8 + plugin fornece cognitiva “sonar-like”, não oficial.
- A stdlib fornece AST, auditoria e importlib; são a base do grafo e do runtime.
- Tarjan, BFS e as métricas de coesão/CBO foram implementados e validados.
- `ProjectValidator` verifica conformidade, mas só das regras ativas.
- O que não foi usado está declarado; isso delimita as conclusões.

**Próximo:** [Capítulo 8](capitulo-08-resultados-solar.md) — os resultados do SOLAR, organizados por categoria.
