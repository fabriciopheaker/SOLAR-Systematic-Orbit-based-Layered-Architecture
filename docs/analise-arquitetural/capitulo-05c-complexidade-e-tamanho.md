# Capítulo 5C — Catálogo: complexidade, tamanho, Halstead e MI

> Continuação do catálogo. As fichas seguem os mesmos 18 campos do [Capítulo 5A](capitulo-05a-acoplamento-e-ciclos.md).

---

## 5.5 Complexidade ciclomática (CC)

| #   | Campo                               | Conteúdo                                                                                                                                                                               |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Complexidade ciclomática                                                                                                                                                               |
| 2   | Nome original                       | _Cyclomatic Complexity_                                                                                                                                                                |
| 3   | Sigla                               | **CC** — _Cyclomatic Complexity_                                                                                                                                                       |
| 4   | Categoria                           | complexidade                                                                                                                                                                           |
| 5   | O que é, em linguagem simples       | Conta quantos caminhos independentes existem em uma função. Quanto mais decisões, mais caminhos.                                                                                       |
| 6   | O que mede exatamente               | Número de caminhos linearmente independentes no grafo de fluxo de controle: `CC = E − N + 2P` (arestas, nós, componentes conectados) ou, na prática, `1 + número de decisões`.         |
| 7   | Por que é importante                | Mais caminhos significam mais casos de teste, mais esforço de leitura e maior chance de um caminho não ser exercitado.                                                                 |
| 8   | Como é calculado                    | Soma-se 1 à contagem de `if`, `for`, `while`, `except`, `with` (quando conta como bloco), `case`, `assert`, `and`/`or` e comprehensions com filtro, conforme a implementação.          |
| 9   | Como interpretar                    | 1–5: baixa; 6–10: moderada; 11–20: alta; >20: muito alta (ranks do Radon). Esses limites são convenção da ferramenta, não lei.                                                         |
| 10  | Cenário favorável                   | Mediana baixa e nenhuma função em rank alto.                                                                                                                                           |
| 11  | Cenário potencialmente desfavorável | Função com CC alto e muitas responsabilidades; função com CC alto e poucos testes.                                                                                                     |
| 12  | Exemplo numérico                    | `def f(x): if x > 0 and x < 10: return 1; return 0` tem decisões `if` + `and` → CC = 1 + 2 = 3.                                                                                        |
| 13  | Exemplo no SOLAR                    | 553 funções de produção; soma 1.278; média 2,31; mediana 2; P90 5; máximo 10 (`ErrorExposureScanner._destination`). 523 funções no rank A (94,6%) e 30 no rank B; nenhuma em C–F.      |
| 14  | Limitações                          | Não mede complexidade de dados, de estado ou de domínio; `and`/`or` contam como decisões; `try/except` e `with` variam por implementação; uma função longa e linear pode ter CC baixo. |
| 15  | Erros comuns                        | Dizer que CC baixo garante código simples (veja `Kernel.mount`, 163 linhas e CC 2); comparar CC de funções de tamanhos muito diferentes; usar 10 como limite universal.                |
| 16  | Ferramenta/procedimento no SOLAR    | Radon 6.0.1 (`cc`); `funcoes_complexidade.csv`; validação independente V3 (soma 1.278 e máximo 10 exatos).                                                                             |
| 17  | Status                              | **VALIDADO** (recálculo independente exato).                                                                                                                                           |
| 18  | O que se pode/não se pode concluir  | Pode-se medir caminhos e identificar outliers. Não se pode concluir presença de defeito, dificuldade real de manutenção ou qualidade do contrato.                                      |

### 5.5.1 CC × tamanho: o caso `Kernel.mount`

`Kernel.mount` tem **163 linhas** e **CC 2**. É um exemplo de que complexidade e tamanho são dimensões diferentes: o método é longo porque lista muitos passos de composição, mas tem poucas decisões. Dizer “é complexo” por causa do tamanho e “é simples” por causa da CC são duas leituras parciais. A leitura correta combina as duas: **longo e linear**.

O inverso também existe: uma função curta com muitos `if` aninhados pode ter CC alto e ser difícil de ler.

### 5.5.2 O topo da distribuição

| Função                               | CC  | Linhas | Leitura                                            |
| ------------------------------------ | --- | ------ | -------------------------------------------------- |
| `ErrorExposureScanner._destination`  | 10  | 85     | maior CC; também maior complexidade cognitiva (18) |
| `ErrorLog.record`                    | 9   | 28     | CC alta em pouco código: muitos ramos              |
| `ControllerReturnScanner._scan_file` | 8   | 58     | varredura com vários casos                         |
| `ErrorExposureScanner._detail`       | 8   | 39     | ramos de detalhe                                   |
| `Identity._persist`                  | 7   | 51     | ramos de persistência                              |

Nenhum caso ultrapassa 10. A cauda é curta: 30 funções no rank B, nenhuma acima.

---

## 5.6 Complexidade cognitiva

| #   | Campo                               | Conteúdo                                                                                                                                                                                                           |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Nome em português                   | Complexidade cognitiva                                                                                                                                                                                             |
| 2   | Nome original                       | _Cognitive Complexity_                                                                                                                                                                                             |
| 3   | Sigla                               | não há sigla universal; no projeto usa-se **cognitiva**                                                                                                                                                            |
| 4   | Categoria                           | complexidade                                                                                                                                                                                                       |
| 5   | O que é, em linguagem simples       | Tenta medir o **esforço de entender** o código, penalizando aninhamento, quebras de fluxo e sequências de condições.                                                                                               |
| 6   | O que mede exatamente               | Soma de incrementos: +1 para cada estrutura de controle, +1 extra por nível de aninhamento, +1 para sequências de operadores lógicos, +1 para recursão e quebras de fluxo.                                         |
| 7   | Por que é importante                | Dois códigos com a mesma CC podem ter esforços de leitura muito diferentes se um for plano e o outro profundamente aninhado.                                                                                       |
| 8   | Como é calculado                    | Implementação `flake8-cognitive-complexity` 0.1.0, que segue o modelo “sonar-like”: incrementos por estrutura e aninhamento.                                                                                       |
| 9   | Como interpretar                    | Valores baixos: leitura direta. Valores altos: leitura em camadas. O Sonar usa 15 como limiar padrão da regra S3776; é convenção, não universal.                                                                   |
| 10  | Cenário favorável                   | Mediana baixa e nenhum caso acima de 15.                                                                                                                                                                           |
| 11  | Cenário potencialmente desfavorável | Função acima de 15, especialmente se também tiver CC alta e poucos testes.                                                                                                                                         |
| 12  | Exemplo numérico                    | `if x > 0 and y > 0:` dentro de um `for`: `for` (+1), `if` (+1 +1 de aninhamento), sequência `and` (+1) = 4.                                                                                                       |
| 13  | Exemplo no SOLAR                    | 300 funções com valor > 0, em 96 módulos; soma 794; média 2,65; mediana 2; P90 6; máximo 18 (`_destination`). Apenas 1 função acima de 15; 2 acima de 10 (`_scan_file` 14, `_verifies_signature` 13).              |
| 14  | Limitações                          | Implementação de terceiros, não oficial do Sonar; não mede complexidade de domínio; depende das regras de incremento; funções com valor 0 não aparecem no CSV; não é comparável numericamente com o Sonar oficial. |
| 15  | Erros comuns                        | Tratar o valor do plugin como idêntico ao Sonar; usar 15 como verdade absoluta; ignorar que só 300 funções têm valor > 0; comparar com CC como se fossem a mesma escala.                                           |
| 16  | Ferramenta/procedimento no SOLAR    | `flake8` 7.4.1 + `flake8-cognitive-complexity` 0.1.0; `complexidade_cognitiva.csv`; validação independente V8 (soma 794 e máximo 18 exatos).                                                                       |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (soma e máximo conferidos; semântica “sonar-like”, não oficial).                                                                                                                        |
| 18  | O que se pode/não se pode concluir  | Pode-se identificar esforço de leitura e outliers. Não se pode afirmar equivalência com o Sonar oficial nem que 18 seja “ruim” em termos absolutos.                                                                |

### 5.6.1 Onde está a complexidade cognitiva

| Camada          | Funções | Soma    | Participação |
| --------------- | ------- | ------- | ------------ |
| Nucleus         | 278     | 752     | 94,7%        |
| Observatory     | 13      | 30      | 3,8%         |
| Bootstrap       | 3       | 5       | 0,6%         |
| Orbits/Planets  | 4       | 5       | 0,6%         |
| Orbits/Database | 2       | 2       | 0,3%         |
| Orbits          | 0       | 0       | 0%           |
| **Total**       | **300** | **794** | **100%**     |

A concentração no Nucleus é coerente com o papel da camada: scanners, regras e middleware fazem muitas verificações condicionais. Não é, por si, um problema; é o centro de decisão do sistema.

### 5.6.2 `_destination`: CC 10, cognitiva 18

- 85 linhas, 10 caminhos independentes, 18 pontos de esforço cognitivo.
- É o único caso acima de 15.
- Leitura: **merece investigação**, especialmente porque combina CC alta, cognitiva alta e tamanho médio-alto.
- O que não se pode concluir: que a função tenha defeito. O achado é de **risco de manutenção e teste**, não de corretude.

---

## 5.7 Tamanho: LOC, SLOC e LLOC

| #   | Campo                               | Conteúdo                                                                                                                                                                                                       |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Linhas de código; linhas físicas; linhas lógicas                                                                                                                                                               |
| 2   | Nome original                       | _Lines of Code_; _Source Lines of Code_; _Logical Lines of Code_                                                                                                                                               |
| 3   | Sigla                               | **LOC**, **SLOC**, **LLOC**                                                                                                                                                                                    |
| 4   | Categoria                           | tamanho                                                                                                                                                                                                        |
| 5   | O que é, em linguagem simples       | Quanto texto de código existe. LOC conta linhas físicas; SLOC desconta linhas em branco e comentários; LLOC conta instruções lógicas.                                                                          |
| 6   | O que mede exatamente               | **LOC:** todas as linhas. **SLOC:** linhas com código, excluindo branco e comentário. **LLOC:** instruções (uma atribuição, um `if`, um `return` etc.).                                                        |
| 7   | Por que é importante                | Tamanho é um dos componentes do MI e um indicador de esforço de leitura e de chance de erro.                                                                                                                   |
| 8   | Como é calculado                    | Radon `raw`: `loc`, `sloc`, `lloc`, `comments`, `multi`, `blank`.                                                                                                                                              |
| 9   | Como interpretar                    | Compare com o P90 e com o papel do módulo. Arquivos de configuração/composição tendem a ser maiores.                                                                                                           |
| 10  | Cenário favorável                   | Funções e módulos dentro da faixa típica do projeto.                                                                                                                                                           |
| 11  | Cenário potencialmente desfavorável | Módulo muito acima do P90 com muitas responsabilidades.                                                                                                                                                        |
| 12  | Exemplo numérico                    | Um arquivo com 10 linhas, 3 em branco, 2 comentários e 5 instruções: LOC = 10, SLOC = 5, LLOC = 5.                                                                                                             |
| 13  | Exemplo no SOLAR                    | Funções: mínimo 2, mediana 13, média 16,6, P90 35, máximo 163 (`Kernel.mount`). 76 funções > 30 linhas (13,7%), 12 > 50 (2,2%), 2 > 100 (0,4%). `project_validator`: LOC 423, SLOC 269, LLOC 107.              |
| 14  | Limitações                          | LOC é sensível a estilo (quebras de linha, comentários); LLOC depende da definição de instrução; tamanho não mede complexidade; SLOC pode não somar o total do arquivo por causa de código no nível de módulo. |
| 15  | Erros comuns                        | Comparar LOC com SLOC; tratar arquivo grande como arquivo complexo; somar SLOC de funções e esperar o SLOC do módulo.                                                                                          |
| 16  | Ferramenta/procedimento no SOLAR    | Radon `raw`; `modulos_metricas.csv` e `tamanho` no resumo; validação V2 (8 módulos conferidos).                                                                                                                |
| 17  | Status                              | **VALIDADO** (método e amostra).                                                                                                                                                                               |
| 18  | O que se pode/não se pode concluir  | Pode-se medir esforço de leitura e localizar outliers. Não se pode concluir qualidade, coesão ou complexidade apenas pelo tamanho.                                                                             |

### 5.7.1 Por que o detalhe não soma o total

Em `project_validator`, a soma das linhas das funções é 372, mas o LOC do módulo é 423. A diferença de 51 linhas vem de código fora de funções: constante, imports, decoradores e definições auxiliares. **Isso não é erro**: são granularidades diferentes. Somar funções não reconstrói o arquivo.

### 5.7.2 Tamanho × complexidade no topo

| Função                           | Linhas | CC  | Leitura                               |
| -------------------------------- | ------ | --- | ------------------------------------- |
| `Kernel.mount`                   | 163    | 2   | longo e linear: composição            |
| `ArchitectureScanner._scan_file` | 108    | 6   | longo e moderadamente ramificado      |
| `_resolve_import`                | 85     | 4   | longo e linear                        |
| `_destination`                   | 85     | 10  | longo e ramificado                    |
| `project_checks`                 | 81     | 1   | longo e linear: lista de verificações |

A leitura conjunta evita dois erros: chamar `mount` de “complexo” por ser longo e chamar `_destination` de “simples” por ter 85 linhas.

---

## 5.8 Métricas de Halstead

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                                                            |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Métricas de Halstead (volume, dificuldade, esforço)                                                                                                                                                                                                                 |
| 2   | Nome original                       | _Halstead metrics_                                                                                                                                                                                                                                                  |
| 3   | Sigla                               | não há sigla única; usa-se **Halstead**                                                                                                                                                                                                                             |
| 4   | Categoria                           | tamanho/complexidade (família própria)                                                                                                                                                                                                                              |
| 5   | O que é, em linguagem simples       | Conta operadores e operandos para estimar o “volume” de informação de um trecho de código.                                                                                                                                                                          |
| 6   | O que mede exatamente               | `n1` operadores distintos, `n2` operandos distintos, `N1` total de operadores, `N2` total de operandos. Vocabulário `n = n1 + n2`; comprimento `N = N1 + N2`; volume `V = N · log₂ n`; dificuldade `D = (n1/2) · (N2/n2)`; esforço `E = D · V`.                     |
| 7   | Por que é importante                | O volume entra no cálculo do MI e ajuda a estimar esforço de leitura.                                                                                                                                                                                               |
| 8   | Como é calculado                    | Radon percorre a AST e conta operadores/operandos. A implementação **não visita `Call` e `Subscript`**, o que zera funções que só chamam métodos ou indexam estruturas.                                                                                             |
| 9   | Como interpretar                    | Volume alto: mais informação para ler. Zero: a métrica não conseguiu contar (não significa código vazio).                                                                                                                                                           |
| 10  | Cenário favorável                   | Valores calculados para a maioria das funções e coerentes com o tamanho.                                                                                                                                                                                            |
| 11  | Cenário potencialmente desfavorável | Muitas funções com zero, distorcendo o volume total e o MI.                                                                                                                                                                                                         |
| 12  | Exemplo numérico                    | `x = a + b` e `y = x * 2`: operadores `=, +, =, *` → n1 = 3, N1 = 4; operandos `x, a, b, y, x, 2` → n2 = 5, N2 = 6; n = 8, N = 10, V = 10 · log₂ 8 = 30.                                                                                                            |
| 13  | Exemplo no SOLAR                    | Volume total 19.918,75; produção 6.094,74 (30,6%); testes 13.824,01. Funções com `n1 = n2 = 0`: 291 de 553 na produção (52,62%); 561 de 1.233 na API (45,50%); 548 de 1.219 no JSON (44,95%). `ErrorLog`: 8 de 12 funções com zero.                                 |
| 14  | Limitações                          | Definição de operador/operando é ambígua; a implementação do Radon não conta chamadas nem indexação; volume não mede complexidade de controle; não é comparável entre linguagens; o JSON perde 14 homônimos (1 na produção: `status` em `nucleus/rules/report.py`). |
| 15  | Erros comuns                        | Tratar `V = 0` como função trivial; usar volume total para comparar produção e testes; interpretar Halstead como prova de qualidade.                                                                                                                                |
| 16  | Ferramenta/procedimento no SOLAR    | Radon `hal`; `radon_halstead_modulos.csv`; validação independente V4 (volume e zeros).                                                                                                                                                                              |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (cálculo fiel ao Radon; cobertura incompleta por limitação do visitor).                                                                                                                                                                  |
| 18  | O que se pode/não se pode concluir  | Pode-se usar o volume no MI e comparar módulos com a mesma limitação. Não se pode usar Halstead como medida completa de complexidade nem tratar zero como ausência de código.                                                                                       |

### 5.8.1 O que o zero significa

Quando uma função só faz chamadas (`self._x(...)`) ou acessos (`obj.attr`), o visitor do Radon pode não registrar operadores/operandos e devolver `n1 = n2 = 0`. O volume vira 0 e o MI do arquivo sobe. **Zero é uma falha de representação, não uma propriedade do código.**

### 5.8.2 Impacto no MI

Como o MI usa `ln(V)`, um volume zero faz o termo `5,2 · ln(V)` desaparecer e o MI ser calculado como se o arquivo fosse trivial. Em `http_input`, o MI é 32,26; recalculando sem docstrings como comentário, sobe para 79,88. A diferença não vem de mudança no código, mas da forma de contar.

---

## 5.9 Índice de Manutenibilidade (MI)

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                                                                                     |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Índice de manutenibilidade                                                                                                                                                                                                                                                                   |
| 2   | Nome original                       | _Maintainability Index_                                                                                                                                                                                                                                                                      |
| 3   | Sigla                               | **MI** — _Maintainability Index_                                                                                                                                                                                                                                                             |
| 4   | Categoria                           | manutenibilidade                                                                                                                                                                                                                                                                             |
| 5   | O que é, em linguagem simples       | Um número de 0 a 100 que tenta resumir o esforço de manter um módulo, combinando volume, complexidade, tamanho e comentários.                                                                                                                                                                |
| 6   | O que mede exatamente               | `MI = max(0, min(100, (171 − 5,2·ln V − 0,23·CC − 16,2·ln LLOC + 50·sen(√(2,46·rad(%comentários)))) · 100/171))`; 100 quando `V ≤ 0` ou `LLOC ≤ 0`.                                                                                                                                          |
| 7   | Por que é importante                | É uma métrica composta usada para triagem e para acompanhar evolução.                                                                                                                                                                                                                        |
| 8   | Como é calculado                    | Radon `mi_visit(fonte, multi=True)`; `V` é o volume de Halstead do arquivo, `CC` é a complexidade total do arquivo, `LLOC` é o número de linhas lógicas e `%comentários = (comments + multi) / sloc · 100`.                                                                                  |
| 9   | Como interpretar                    | Ranks do Radon: A > 19, B 10–19, C < 10. Valores altos indicam, na fórmula, menos volume/complexidade e mais comentários.                                                                                                                                                                    |
| 10  | Cenário favorável                   | MI alto com volume e complexidade reais (não por volume zero).                                                                                                                                                                                                                               |
| 11  | Cenário potencialmente desfavorável | MI baixo com volume e complexidade altos; ou MI artificialmente alto por volume zero.                                                                                                                                                                                                        |
| 12  | Exemplo numérico                    | `V = 1.000`, `CC = 10`, `LLOC = 50`, 10% de comentários: `5,2·ln 1000 = 35,92`; `0,23·10 = 2,3`; `16,2·ln 50 = 63,36`; `50·sen(√(2,46·0,1745)) = 30,45`; `(171 − 35,92 − 2,3 − 63,36 + 30,45)·100/171 ≈ 58,4`. Sem comentários, o mesmo código daria ≈ 40,6.                                 |
| 13  | Exemplo no SOLAR                    | 269 arquivos, todos rank A; média 84,53; mediana 87,82; mínimo 32,26. Produção: média 88,14; mediana 100; 110 de 208 módulos com MI = 100, dos quais 50 têm SLOC > 0. Sensibilidade: com `count_multi=False`, 26 módulos variam mais de 10 pontos; média +2,87; máximo +47,62; mínimo 50,35. |
| 14  | Limitações                          | O termo de comentários pode dominar o resultado; volume zero satura o MI em 100; a fórmula foi calibrada em outro contexto; não mede qualidade de projeto, testes ou domínio; não é comparável entre ferramentas sem a mesma fórmula.                                                        |
| 15  | Erros comuns                        | Dizer “MI 100 = código perfeito”; comparar MI de módulos com e sem docstrings; usar MI como único critério de priorização; ignorar a saturação.                                                                                                                                              |
| 16  | Ferramenta/procedimento no SOLAR    | Radon 6.0.1 (`mi`); `modulos_metricas.csv`; validação V9 (recomputação oficial, 0 divergências) e análise de sensibilidade.                                                                                                                                                                  |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (fórmula reproduzida; poder de discriminação limitado).                                                                                                                                                                                                           |
| 18  | O que se pode/não se pode concluir  | Pode-se reproduzir o MI e comparar módulos com a mesma configuração. Não se pode usar o MI como prova de manutenibilidade real nem ordenar módulos por ele quando a saturação está presente.                                                                                                 |

### 5.9.1 Por que 110 módulos têm MI 100

Dos 208 módulos de produção, 110 atingem 100. Desses, 50 têm SLOC > 0 e chegam a 100 porque `V = 0` (limitação do Halstead) ou porque a combinação de volume/complexidade/tamanho é baixa o suficiente para saturar. Os outros 60 têm SLOC = 0: 59 inicializadores de pacote e 1 arquivo vazio.

**Consequência:** o MI não ordena 110 módulos distintos; ele os colapsa no mesmo valor. Para priorização, use CC, cognitiva, tamanho e acoplamento em conjunto.

### 5.9.2 O caso `http_input`

- MI oficial: 32,26 (o menor do projeto).
- Com `count_multi=False`: 79,88.
- Motivo: 393,33% de comentários em relação ao SLOC (docstrings contadas como comentário), o que infla o termo seno.
- Leitura: o valor baixo **não** indica código ruim; indica sensibilidade da fórmula a comentários.
- **Lição:** um outlier de MI exige inspeção da composição, não conclusão imediata.

### 5.9.3 MI como indicador composto

O MI é útil como **triagem**, não como veredito. Ele combina métricas com limitações próprias; quando uma delas falha (Halstead zero, comentários), o composto herda a falha. Por isso a documentação trata o MI como **validado com ressalvas** e sempre o acompanha de CC, Halstead e tamanho.

---

## Fechamento do bloco

- CC mede caminhos; cognitiva mede esforço de leitura; tamanho mede extensão. Nenhuma substitui as outras.
- Halstead tem cobertura incompleta nesta implementação; zero não é trivialidade.
- MI é composto e satura; use-o com contexto e nunca isolado.
- Os outliers (`_destination`, `Kernel.mount`, `http_input`) são pontos de inspeção, não condenações.

**Próximo:** [Capítulo 5D](capitulo-05d-analises-adicionais.md) — NOM, NOC, reprodutibilidade, runtime e `ProjectValidator`.
