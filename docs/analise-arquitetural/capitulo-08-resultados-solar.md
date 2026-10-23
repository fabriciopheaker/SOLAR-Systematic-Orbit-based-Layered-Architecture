# Capítulo 8 — Resultados do SOLAR

> **Pergunta deste capítulo:** o que foi medido, com que número, em qual conjunto e com qual leitura?

**Regra desta seção:** cada resultado é apresentado com sete itens — **métrica, valor, unidade/denominador, escopo, status, leitura e limite**. Nenhum número aparece sem o conjunto a que pertence.

---

## 8.1 Escopo e corpus

| Métrica                | Valor  | Unidade/denominador | Escopo                       | Status   | Leitura                        | Limite                                                 |
| ---------------------- | ------ | ------------------- | ---------------------------- | -------- | ------------------------------ | ------------------------------------------------------ |
| Arquivos `.py`         | 269    | arquivos            | projeto inteiro              | validado | corpus completo                | não inclui arquivos não-Python                         |
| Módulos de produção    | 208    | módulos             | exclui `tests/`              | validado | 148 com código, 60 sem código  | “módulo” = arquivo importável                          |
| Módulos de teste       | 61     | módulos             | `tests/`                     | validado | separados da produção          | não entram nas métricas de produção                    |
| SLOC de produção       | 6.261  | linhas              | 208 módulos (148 com código) | validado | tamanho real do código         | SLOC não conta comentários/branco                      |
| SLOC de testes         | 5.524  | linhas              | 61 módulos                   | validado | quase o tamanho da produção    | não misturar com produção                              |
| SLOC total             | 11.785 | linhas              | 269 módulos                  | validado | soma dos dois conjuntos        | —                                                      |
| Classes de produção    | 136    | classes             | exclui testes                | validado | 124 regulares + 12 utilitárias | 9 herdam de ABC/Protocol                               |
| Classes de teste       | 29     | classes             | `tests/`                     | validado | separadas                      | —                                                      |
| Funções de produção    | 553    | funções/métodos     | exclui testes                | validado | base das métricas de função    | inclui funções de módulo e métodos; não inclui lambdas |
| Funções de teste       | 680    | funções             | `tests/`                     | validado | base separada                  | —                                                      |
| Arestas internas       | 306    | arestas             | produção                     | validado | 304 estáticas + 2 dinâmicas    | não inclui externas                                    |
| Imports externos       | 234    | statements          | 171 na produção              | validado | bibliotecas e stdlib           | não são acoplamento interno                            |
| Imports não resolvidos | 0      | imports             | produção                     | validado | grafo completo para o método   | imports condicionais podem escapar                     |

**Leitura:** o corpus é pequeno e altamente concentrado no Nucleus. Qualquer média geral é puxada por essa camada.

---

## 8.2 Acoplamento

| Métrica               | Valor       | Unidade/denominador   | Escopo                 | Status                 | Leitura                   | Limite                       |
| --------------------- | ----------- | --------------------- | ---------------------- | ---------------------- | ------------------------- | ---------------------------- |
| Ca máximo             | 38          | módulos dependentes   | `solar_exception`      | validado               | hub de exceção            | esperado pelo papel          |
| Ca = 0                | 70          | módulos               | produção               | validado               | folhas/inits/não usados   | não é código morto           |
| Ce máximo             | 49          | módulos importados    | `project_validator`    | validado               | registro de regras        | esperado pelo papel          |
| Ce = 0                | 107         | módulos               | produção               | validado               | módulos folha             | —                            |
| Ce médio              | 3,03        | módulos               | 101 módulos com Ce > 0 | validado               | baixo/moderado            | média sem os 107 zeros       |
| Ce mediano            | 3           | módulos               | 101                    | validado               | metade tem ≤ 3            | —                            |
| Ce P90                | 4           | módulos               | 101                    | validado               | cauda curta               | outlier 49                   |
| I indefinido          | 60          | módulos               | 148 com código         | validado               | 59 inits + `token`        | `0/0` não é zero             |
| I = 1                 | 10          | módulos               | 148                    | validado               | só saída                  | —                            |
| I ≥ 0,8               | 20          | módulos               | 148                    | validado               | instáveis                 | —                            |
| I ≤ 0,2               | 50          | módulos               | 148                    | validado               | estáveis                  | —                            |
| Densidade do grafo    | 0,71%       | arestas possíveis     | 306 / (208·207)        | validado               | grafo esparso             | —                            |
| Arestas intra-camada  | 276 (90,2%) | arestas               | 306                    | validado               | maioria fica na camada    | —                            |
| Arestas entre camadas | 30 (9,8%)   | arestas               | 306                    | validado               | poucas travessias         | —                            |
| CBO médio             | 1,54        | classes referenciadas | 136 classes            | validado com ressalvas | baixo                     | aproximação AST              |
| CBO mediano           | 1           | classes               | 136                    | validado com ressalvas | típico                    | —                            |
| CBO P90               | 3           | classes               | 136                    | validado com ressalvas | cauda curta               | —                            |
| CBO máximo            | 15          | classes               | `Kernel`               | validado com ressalvas | composition root          | não é defeito                |
| CBO externo máximo    | 8           | classes externas      | `DriverSQLAlchemy`     | heurístico             | dependência de SQLAlchemy | não comparável a CBO interno |
| Ambiguidade de CBO    | 0           | nomes                 | 136 classes            | validado               | sem faixa min/max         | —                            |

**Leitura:** o acoplamento interno é baixo e concentrado em poucos hubs com papel arquitetural. Os números altos (`project_validator`, `Kernel`, `solar_exception`) são estruturais, não acidentais.

---

## 8.3 Coesão

| Métrica                    | Valor | Unidade/denominador | Escopo                 | Status   | Leitura                          | Limite              |
| -------------------------- | ----- | ------------------- | ---------------------- | -------- | -------------------------------- | ------------------- |
| Classes com LCOM aplicável | 39    | classes             | 136                    | validado | 28,7%                            | 97 N/A              |
| LCOM1 mediana              | 3     | pares               | 39                     | validado | típico                           | cresce com métodos  |
| LCOM1 média                | 10,82 | pares               | 39                     | validado | assimétrica                      | outlier 89          |
| LCOM1 P90                  | 28    | pares               | 39                     | validado | cauda                            | —                   |
| LCOM1 máximo               | 89    | pares               | `ErrorExposureScanner` | validado | 14 métodos, 1 atributo           | não é “classe ruim” |
| LCOM4 média                | 1,13  | componentes         | 39                     | validado | quase todas conectadas           | —                   |
| LCOM4 máximo               | 3     | componentes         | `DriverSQLAlchemy`     | validado | 3 grupos                         | merece investigação |
| LCOM4 > 1                  | 4     | classes             | 39                     | validado | 10,3%                            | candidatos          |
| TCC mediana                | 0,30  | proporção           | 39                     | validado | baixa conexão direta             | —                   |
| TCC média                  | 0,398 | proporção           | 39                     | validado | moderada-baixa                   | —                   |
| LCOM\* mediana             | 0,75  | proporção           | 39                     | validado | alta falta de coesão normalizada | —                   |
| LCOM\* média               | 0,651 | proporção           | 39                     | validado | idem                             | —                   |
| LCOM\* máximo              | 1,0   | proporção           | 39                     | validado | métodos usam 1 atributo          | saturação           |
| N/A: < 2 métodos           | 54    | classes             | 136                    | validado | sem domínio                      | não é “coesa”       |
| N/A: sem atributos         | 42    | classes             | 136                    | validado | estado de classe/fachada         | não é “incoesa”     |
| N/A: sem uso de estado     | 1     | classe              | 136                    | validado | estado declarado e não usado     | —                   |

**Leitura:** a maioria das classes não tem domínio válido para LCOM. Nas 39 válidas, a coesão de estado é baixa em mediana, mas LCOM4 mostra que os métodos costumam estar conectados por chamadas. As duas leituras não se contradizem: **conexão ≠ compartilhamento de estado**.

---

## 8.4 Complexidade

| Métrica                 | Valor       | Unidade/denominador | Escopo             | Status                 | Leitura                | Limite                   |
| ----------------------- | ----------- | ------------------- | ------------------ | ---------------------- | ---------------------- | ------------------------ |
| CC total                | 1.278       | soma                | 553 funções        | validado               | —                      | —                        |
| CC média                | 2,31        | caminhos            | 553                | validado               | baixa                  | assimétrica              |
| CC mediana              | 2           | caminhos            | 553                | validado               | típica baixa           | —                        |
| CC P90                  | 5           | caminhos            | 553                | validado               | cauda curta            | —                        |
| CC máxima               | 10          | caminhos            | `_destination`     | validado               | rank B                 | nenhum rank C–F          |
| Rank A                  | 523 (94,6%) | funções             | 553                | validado               | maioria simples        | rank é convenção         |
| Rank B                  | 30 (5,4%)   | funções             | 553                | validado               | moderadas              | —                        |
| Cognitiva: funções > 0  | 300         | funções             | 553                | validado com ressalvas | 96 módulos             | plugin “sonar-like”      |
| Cognitiva: soma         | 794         | pontos              | 300                | validado com ressalvas | —                      | —                        |
| Cognitiva: mediana      | 2           | pontos              | 300                | validado com ressalvas | baixa                  | —                        |
| Cognitiva: média        | 2,65        | pontos              | 300                | validado com ressalvas | assimétrica            | —                        |
| Cognitiva: P90          | 6           | pontos              | 300                | validado com ressalvas | cauda                  | —                        |
| Cognitiva: máximo       | 18          | pontos              | `_destination`     | validado com ressalvas | único > 15             | limiar Sonar é convenção |
| Cognitiva > 15          | 1           | função              | 300                | validado com ressalvas | outlier                | —                        |
| Cognitiva no Nucleus    | 752 (94,7%) | pontos              | 794                | validado com ressalvas | concentração           | esperado pelo papel      |
| Ramos = CC − 1          | 22 de 35    | alertas             | amostra de alertas | parcial                | maioria compatível     | 13 divergem              |
| Aninhamento reproduzido | 2 de 35     | alertas             | amostra            | parcial                | quase não reproduzível | não usar como prova      |

**Leitura:** a complexidade de controle é baixa na maior parte do código e se concentra em scanners do Nucleus. O único outlier de cognitiva é `_destination`.

---

## 8.5 Tamanho

| Métrica                     | Valor                           | Unidade/denominador | Escopo                 | Status   | Leitura                   | Limite                          |
| --------------------------- | ------------------------------- | ------------------- | ---------------------- | -------- | ------------------------- | ------------------------------- |
| Função: mínimo              | 2                               | linhas              | 553                    | validado | —                         | —                               |
| Função: mediana             | 13                              | linhas              | 553                    | validado | típica                    | —                               |
| Função: média               | 16,6                            | linhas              | 553                    | validado | assimétrica               | —                               |
| Função: P90                 | 35                              | linhas              | 553                    | validado | cauda                     | —                               |
| Função: máximo              | 163                             | linhas              | `Kernel.mount`         | validado | longo e linear (CC 2)     | tamanho ≠ complexidade          |
| Funções > 30 linhas         | 76 (13,7%)                      | funções             | 553                    | validado | cauda relevante           | —                               |
| Funções > 50 linhas         | 12 (2,2%)                       | funções             | 553                    | validado | poucas                    | —                               |
| Funções > 100 linhas        | 2 (0,4%)                        | funções             | 553                    | validado | `mount`, `_scan_file`     | —                               |
| LOC de `project_validator`  | 423                             | linhas              | módulo                 | validado | maior módulo              | —                               |
| SLOC de `project_validator` | 269                             | linhas              | módulo                 | validado | —                         | —                               |
| LLOC de `project_validator` | 107                             | instruções          | módulo                 | validado | —                         | —                               |
| Soma das funções vs LOC     | 372 vs 423                      | linhas              | `project_validator`    | validado | 51 linhas fora de funções | granularidades diferentes       |
| NOM máximo                  | 14 (sem especiais) / 15 (total) | métodos             | `ErrorExposureScanner` | validado | maior classe              | variante declarada              |
| NOC de produção             | 136                             | classes             | projeto                | validado | 124 + 12                  | weighted 127,6 não reproduzível |

**Leitura:** o código é composto por muitas funções curtas e poucas funções longas. As duas funções acima de 100 linhas são de composição/varredura e merecem leitura, não condenação automática.

---

## 8.6 Manutenibilidade

| Métrica                 | Valor       | Unidade/denominador | Escopo       | Status                 | Leitura          | Limite                 |
| ----------------------- | ----------- | ------------------- | ------------ | ---------------------- | ---------------- | ---------------------- |
| MI médio (todos)        | 84,53       | 0–100               | 269 módulos  | validado com ressalvas | alto             | saturação              |
| MI mediano (todos)      | 87,82       | 0–100               | 269          | validado com ressalvas | alto             | —                      |
| MI mínimo               | 32,26       | 0–100               | `http_input` | validado com ressalvas | outlier          | sensível a comentários |
| MI médio (produção)     | 88,14       | 0–100               | 208          | validado com ressalvas | alto             | —                      |
| MI mediano (produção)   | 100         | 0–100               | 208          | validado com ressalvas | saturação        | não discrimina         |
| MI = 100                | 110 (52,9%) | módulos             | 208          | validado com ressalvas | 50 com SLOC > 0  | volume zero            |
| Rank A                  | 269 (100%)  | módulos             | 269          | validado com ressalvas | todos            | rank não é qualidade   |
| Sensibilidade: Δ > 10   | 26          | módulos             | 208          | validado com ressalvas | fórmula sensível | —                      |
| Sensibilidade: Δ médio  | +2,87       | pontos              | 208          | validado com ressalvas | pequeno na média | —                      |
| Sensibilidade: Δ máximo | +47,62      | pontos              | 208          | validado com ressalvas | grande em casos  | —                      |
| MI mínimo sem multi     | 50,35       | 0–100               | 208          | validado com ressalvas | sobe de 32,26    | comentários dominam    |

**Leitura:** o MI não serve para ordenar módulos do SOLAR: mais da metade satura em 100. Ele serve para mostrar que a fórmula é sensível a volume e comentários — e que “MI alto” não é prova de qualidade.

---

## 8.7 Ciclos

| Métrica          | Valor | Unidade/denominador | Escopo                   | Status                 | Leitura                  | Limite          |
| ---------------- | ----- | ------------------- | ------------------------ | ---------------------- | ------------------------ | --------------- |
| Nós              | 208   | módulos             | produção                 | validado               | —                        | —               |
| Arestas          | 306   | arestas             | produção                 | validado               | 304 + 2 dinâmicas        | —               |
| Ciclos estáticos | 0     | ciclos              | grafo estático           | validado               | grafo acíclico no modelo | não vê dinâmico |
| Ciclos dinâmicos | 1     | ciclo               | `Database ↔ user_model`  | validado com ressalvas | dependência temporal     | 3 cenários      |
| SCCs             | 207   | componentes         | 208 nós                  | validado               | 1 SCC de tamanho 2       | —               |
| Aresta tardia    | 1     | aresta              | `kernel → orbits.routes` | validado               | controle de ordem        | não é ciclo     |
| Auto-arestas     | 0     | arestas             | produção                 | validado               | —                        | —               |

**Leitura:** o grafo estático é acíclico e o runtime revela um ciclo intencional com dependência de ordem. O risco é de inicialização, não de deadlock observado.

---

## 8.8 Alcance e utilização

| Métrica                        | Valor | Unidade/denominador | Escopo                       | Status                 | Leitura                  | Limite             |
| ------------------------------ | ----- | ------------------- | ---------------------------- | ---------------------- | ------------------------ | ------------------ |
| Alcançáveis (estático)         | 134   | módulos             | 208                          | validado               | 133 com código + 1 init  | BFS                |
| Não alcançáveis (estático)     | 74    | módulos             | 208                          | validado               | 59 inits + 15 com código | candidatos         |
| SLOC não alcançável (estático) | 631   | linhas              | 6.261                        | validado               | 10,1%                    | —                  |
| Módulos observados (união)     | 175   | módulos             | 3 cenários                   | validado com ressalvas | 133 com código + 42 pais | cenários limitados |
| Ausentes em runtime            | 14    | módulos             | 15 candidatos                | validado com ressalvas | 625 SLOC                 | 9,98%              |
| Refutados em runtime           | 1     | módulo              | `observatory.records`        | validado               | pacote-pai implícito     | —                  |
| Pais implícitos                | 42    | pacotes             | união                        | validado               | inits vazios             | não são uso        |
| Alcançável não observado       | 1     | módulo              | `observatory.solar.__main__` | validado com ressalvas | não executado            | —                  |

**Leitura:** os 14 ausentes formam um conjunto coerente de segurança de borda e upload. Isso sugere funcionalidade não conectada aos cenários, não código aleatório. **Não é prova de código morto.**

---

## 8.9 Análises complementares

| Métrica                       | Valor                      | Unidade/denominador         | Escopo             | Status      | Leitura                                                                | Limite                           |
| ----------------------------- | -------------------------- | --------------------------- | ------------------ | ----------- | ---------------------------------------------------------------------- | -------------------------------- |
| Alertas estruturais revisados | 60                         | alertas                     | relatório original | validado    | 7 confirmados, 7 FP, 43 parciais, 1 não reproduzível, 2 fora de escopo | detalhe frequentemente não fecha |
| Reprodutibilidade             | hashes idênticos           | execuções                   | 2 execuções        | validado    | determinístico                                                         | após normalização                |
| Validador                     | `correct`                  | 17 verificações / 29 regras | projeto            | informativo | 0 violações                                                            | ROF-003 sem scanner              |
| Regras não registradas        | 1                          | regra                       | `SOLAR-ROF-003`    | validado    | não executada                                                          | conformidade parcial             |
| Versões                       | Radon 6.0.1 / flake8 7.4.1 | —                           | ambiente           | validado    | reprodução possível                                                    | depende do ambiente              |

---

## 8.10 O que os resultados **não** dizem

| Pergunta                      | Resposta                                                      |
| ----------------------------- | ------------------------------------------------------------- |
| “A arquitetura é boa?”        | Nenhuma métrica responde isso sozinha.                        |
| “Há defeitos?”                | As métricas não testam comportamento; não há dados de falhas. |
| “O código é fácil de manter?” | O MI não discrimina; não há estudo com mantenedores.          |
| “Os 14 módulos são inúteis?”  | Não se sabe; ausência em 3 cenários não é prova.              |
| “O ciclo causa problema?”     | Não houve falha observada; há dependência de ordem.           |
| “O código é testado?”         | Não foi medida cobertura nem eficácia dos testes.             |
| “A performance é boa?”        | Não há benchmarks.                                            |
| “A dívida está aumentando?”   | Há uma única fotografia; não há tendência.                    |

---

## 8.11 Resumo do capítulo

- O corpus tem 269 arquivos, 208 módulos de produção e 6.261 SLOC de produção.
- O acoplamento é baixo e concentrado em hubs com papel arquitetural.
- A coesão de estado é baixa nas 39 classes válidas, mas LCOM4 mostra conectividade por chamadas.
- A complexidade de controle é baixa; a cognitiva se concentra em scanners; `_destination` é o único outlier > 15.
- O tamanho é dominado por funções curtas, com duas funções > 100 linhas.
- O MI satura e não ordena módulos.
- Há 1 ciclo dinâmico e 14 módulos ausentes em runtime — achados, não vereditos.

**Próximo:** [Capítulo 9](capitulo-09-classificacao-dos-resultados.md) — como classificar esses resultados sem limites universais.
