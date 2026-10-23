# Análise Arquitetural de Software — Documentação Didática com Estudo de Caso SOLAR

**Versão:** 1.0 — 22/10/2026
**Público-alvo:** pessoas sem experiência prévia em arquitetura de software, métricas, análise estática ou estatística aplicada.
**Estudo de caso:** arquitetura SOLAR (repositório `SOLAR`, Python).
**Base dos resultados:** `observatory/audits/` (seis etapas + benchmark), com destaque para `etapa_2_acoplamento_coesao/`, `etapa_3_complexidade/`, `etapa_4_desempenho/` e `etapa_5_seguranca_isolamento/`.

---

## Como ler esta documentação

Esta documentação foi dividida em capítulos complementares para manter a leitura organizada. O arquivo que você está lendo é o **índice principal**: ele explica as convenções, apresenta o mapa dos capítulos e resume os resultados. Cada capítulo é um arquivo nesta mesma pasta.

**Sugestão de leitura:**

1. Capítulos 1 a 4 — conceitos e método (leitura contínua).
2. Capítulo 5 — catálogo de métricas (consulta; leia na ordem ou vá direto à métrica desejada).
3. Capítulos 6 e 7 — glossário e ferramentas (consulta).
4. Capítulos 8 a 11 — resultados do SOLAR, classificação, limitações e roteiro prático.
5. Capítulo 12 — conclusão e referências.

> **Importante:** esta documentação **não** é publicidade da SOLAR. Ela registra o que foi medido, o que foi concluído, o que é interpretação e o que permanece pendente. Resultados desfavoráveis ou inconclusivos são apresentados como tais.

---

## Convenções: fato, interpretação e pendência

Ao longo do texto, três rótulos são usados de forma consistente:

| Rótulo             | Significado                                                                                | Exemplo                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| **Fato observado** | Número ou comportamento verificável nos artefatos, reproduzível pelo procedimento descrito | “A CC máxima das 553 funções de produção é 10.”                                          |
| **Interpretação**  | Leitura técnica do fato, sujeita a contexto e a hipóteses alternativas                     | “Não há hotspot de ramificação; o maior valor é plausível para um analisador sintático.” |
| **Pendência**      | Informação que falta ou verificação que não foi executada                                  | “O CBO absoluto com resolução de tipos não foi medido.”                                  |

**Escopo “produção”:** todos os arquivos `.py` do projeto **exceto** `tests/`, `docs/`, `docker/`, `reports/`, `htmlcov/` e a pasta de dados `storage/` da raiz. O pacote `nucleus/storage/` **está incluído**, porque é código da arquitetura. Testes são contados separadamente.

**Unidades:** “módulo” = arquivo Python importável (por exemplo, `nucleus.kernel`); “classe” = definição de classe; “função/método” = rotina com corpo; “SLOC” = linhas de código; “LOC” = linhas físicas. Nos arquivos CSV/JSON os decimais usam ponto; neste texto, vírgula.

**Versões do ambiente de medição:** Python 3.14.7, Radon 6.0.1, flake8 7.4.1, flake8-cognitive-complexity 0.1.0, Flask 3.1.3, SQLAlchemy 2.1.1, Alembic 1.20.0.

---

## Mapa da documentação

| Capítulo | Arquivo                                                                                       | Conteúdo                                                                                                                        |
| -------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 1        | [Introdução à análise arquitetural](capitulo-01-introducao.md)                                | arquitetura, qualidade, componentes, dependências, acoplamento, coesão, complexidade, manutenibilidade, evolutividade           |
| 2        | [Como funciona uma auditoria arquitetural](capitulo-02-como-funciona-auditoria.md)            | análise estática e dinâmica, rastreamento de importações, grafos, métricas, inspeção, validação independente, reprodutibilidade |
| 3        | [Como interpretar métricas corretamente](capitulo-03-como-interpretar-metricas.md)            | média, mediana, percentil, distribuição, proporção, linha de base, falso positivo/negativo, correlação e causalidade            |
| 4        | [Categorias das métricas e análises](capitulo-04-categorias-das-metricas.md)                  | oito categorias, perguntas que cada uma responde, relações com o SOLAR                                                          |
| 5A       | [Catálogo — acoplamento e ciclos](capitulo-05a-acoplamento-e-ciclos.md)                       | 5.1 Fan-in (Ca), 5.2 Fan-out (Ce), 5.3 Instabilidade (I), 5.4 CBO, 5.11 grafos, SCC e ciclos                                    |
| 5B       | [Catálogo — coesão e alcance](capitulo-05b-coesao-e-alcance.md)                               | 5.10 coesão, LCOM1, LCOM4, LCOM\*, TCC; 5.12 alcançabilidade e módulos aparentemente não utilizados                             |
| 5C       | [Catálogo — complexidade, tamanho e manutenibilidade](capitulo-05c-complexidade-e-tamanho.md) | 5.5 CC, 5.6 complexidade cognitiva, 5.7 tamanho, 5.8 Halstead, 5.9 MI                                                           |
| 5D       | [Catálogo — análises adicionais](capitulo-05d-analises-adicionais.md)                         | 5.13 NOM, NOC, LOC/SLOC/LLOC, Long File, ramos/aninhamento, reprodutibilidade, tracing de runtime, validador arquitetural       |
| 6        | [Glossário de siglas e termos](capitulo-06-glossario.md)                                      | siglas, nomes originais, traduções e significados                                                                               |
| 7        | [Ferramentas utilizadas](capitulo-07-ferramentas.md)                                          | Radon, flake8-cognitive-complexity, AST, audit hook, scripts próprios, validador SOLAR                                          |
| 8        | [Resultados da auditoria do SOLAR](capitulo-08-resultados-solar.md)                           | números, significado leigo, interpretação, o que não se pode concluir, status                                                   |
| 9        | [Como classificar os resultados](capitulo-09-classificacao-dos-resultados.md)                 | categorias contextuais, linhas de base, ausência de limites universais                                                          |
| 10       | [Limitações e ameaças à validade](capitulo-10-limitacoes.md)                                  | ferramentas, implementações, cobertura, falsos positivos/negativos, métrica × qualidade                                         |
| 11       | [Roteiro prático de avaliação](capitulo-11-roteiro-pratico.md)                                | dez passos e dois exemplos completos                                                                                            |
| 12       | [Conclusão e referências](capitulo-12-conclusao-referencias.md)                               | síntese, referências conceituais e fontes específicas do SOLAR                                                                  |

---

## Mapa rápido das métricas

| Métrica ou análise               | Seção | O que pergunta                                       | Status no SOLAR                                                                               |
| -------------------------------- | ----- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Fan-in (Ca)                      | 5.1   | quantos módulos dependem deste?                      | validado                                                                                      |
| Fan-out (Ce)                     | 5.2   | de quantos módulos este depende?                     | validado                                                                                      |
| Instabilidade (I)                | 5.3   | qual o grau de dependência de saída?                 | validado                                                                                      |
| CBO                              | 5.4   | quantas outras classes esta classe referencia?       | validado com ressalvas (AST)                                                                  |
| Complexidade ciclomática (CC)    | 5.5   | quantos caminhos independentes a função tem?         | validado                                                                                      |
| Complexidade cognitiva           | 5.6   | quanto esforço de leitura o fluxo exige?             | validado com ressalvas (ferramenta)                                                           |
| Tamanho de funções               | 5.7   | quantas linhas cada rotina ocupa?                    | validado                                                                                      |
| Halstead                         | 5.8   | qual o vocabulário/volume de operadores e operandos? | reproduzível; **não aplicável** por função                                                    |
| Índice de manutenibilidade (MI)  | 5.9   | qual o índice composto de manutenibilidade?          | reproduzível; **não aplicável** como discriminador                                            |
| Coesão — LCOM1/LCOM4/LCOM\*/TCC  | 5.10  | os métodos compartilham estado?                      | validado nas 39 classes aplicáveis                                                            |
| Grafos e ciclos (SCC)            | 5.11  | há caminhos circulares de dependência?               | validado com ressalvas (estático + runtime)                                                   |
| Alcançabilidade                  | 5.12  | quais módulos são alcançáveis a partir das entradas? | validado com ressalvas                                                                        |
| NOM, NOC, LOC, ramos             | 5.13  | tamanho e forma de classes/arquivos/métodos          | auditoria do relatório original                                                               |
| Reprodutibilidade e determinismo | 5.13  | os números se repetem?                               | validado                                                                                      |
| Tracing de runtime               | 5.13  | o que é carregado em execução?                       | validado com ressalvas                                                                        |
| Validador arquitetural           | 5.13  | as regras da SOLAR são cumpridas?                    | 0 violações nas 29 regras executadas (ROF-003 sem scanner no `check`, mas com teste unitário) |

---

## Resumo dos resultados (para orientação, não para substituir os capítulos)

| Dimensão                      | Resultado observado                                                                              | Leitura curta                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| Corpus                        | 208 módulos de produção, 6.265 SLOC; 61 arquivos de teste, 5.529 SLOC                            | a produção e os testes foram medidos separadamente              |
| Classes                       | 136 de produção; 29 de teste                                                                     | “módulo” e “classe” não são a mesma contagem                    |
| CC (produção)                 | 553 funções, soma 1.278, média 2,31, mediana 2, máximo 10                                        | nenhuma função acima do rank B do Radon                         |
| Cognitiva                     | 300 funções com escore ≥ 1; máximo 18; 1 acima de 15                                             | um único caso muito acima do restante                           |
| Tamanho                       | mediana 13 linhas; máximo 163 (`Kernel.mount`)                                                   | função longa de composição, com CC 2                            |
| Halstead                      | volume de produção 6.094,74; 291 de 553 funções (52,62%) com N1 = N2 = 0                         | a implementação do Radon não conta chamadas; métrica incompleta |
| MI                            | 208/208 módulos de produção em rank A; 110 com MI = 100 por saturação/volume zero                | não discrimina; não deve ser usado como prova de qualidade      |
| Acoplamento                   | 306 arestas internas; Ce máximo 49; Ca máximo 38                                                 | poucos hubs, direção predominante Planet → Nucleus              |
| Ciclos                        | 0 estáticos; 1 dinâmico (`database` ↔ `user_model`)                                              | confirmado em runtime; intencional, com risco de ordem          |
| Coesão                        | LCOM aplicável em 39 de 136 classes; LCOM4 > 1 em 4                                              | 97 classes não admitem LCOM significativo                       |
| Alcançabilidade               | 14 módulos / 625 SLOC confirmados ausentes em runtime                                            | ausência em três cenários ≠ código morto                        |
| Relatório estrutural original | 60 alertas: 7 confirmados, 7 falsos positivos, 43 parciais, 1 não reproduzível, 2 fora do escopo | problemas de escopo e de detalhamento no relatório original     |

---

## Aviso metodológico

1. **Não existe um número universal que diga “esta arquitetura é boa”.** Limites como os ranks do Radon ou o valor 15 da regra S3776 do Sonar são **convenções de ferramenta**, não leis da engenharia.
2. **Métrica não é teste.** Uma métrica calculada não demonstra que o sistema funciona; um teste funcional não demonstra que a estrutura é saudável.
3. **Reproduzir um número não valida sua interpretação.** Vários resultados do SOLAR são reproduzíveis e, ainda assim, inadequados para concluir qualidade (Halstead e MI são os casos claros).
4. **Ausência de evidência não é evidência de ausência.** Não encontrar um módulo em um cenário de execução não prova que ele seja código morto.
5. **Aproximação deve ser declarada como aproximação.** O CBO do SOLAR é calculado por análise sintática; não é um CBO tipado.

---

## Fontes e verificação

As fontes conceituais e as fontes específicas do SOLAR estão no [Capítulo 12](capitulo-12-conclusao-referencias.md). Todas as fórmulas e números foram conferidos contra os artefatos em `observatory/audits/`, incluindo os JSONs do Radon e a verificação independente. O procedimento passo a passo está no [Capítulo 11](capitulo-11-roteiro-pratico.md).

---

## Verificação final desta documentação

### Arquivos criados

| Arquivo                                       | Papel                                                    |
| --------------------------------------------- | -------------------------------------------------------- |
| `DOCUMENTACAO_ANALISE_ARQUITETURAL.md`        | índice, convenções, mapa e verificação                   |
| `capitulo-01-introducao.md`                   | conceitos                                                |
| `capitulo-02-como-funciona-auditoria.md`      | método                                                   |
| `capitulo-03-como-interpretar-metricas.md`    | estatística aplicada                                     |
| `capitulo-04-categorias-das-metricas.md`      | organização                                              |
| `capitulo-05a-acoplamento-e-ciclos.md`        | catálogo: Ca, Ce, I, CBO, SCC/ciclos                     |
| `capitulo-05b-coesao-e-alcance.md`            | catálogo: LCOM, TCC, alcançabilidade                     |
| `capitulo-05c-complexidade-e-tamanho.md`      | catálogo: CC, cognitiva, tamanho, Halstead, MI           |
| `capitulo-05d-analises-adicionais.md`         | catálogo: NOM, NOC, Long File, ramos, runtime, validador |
| `capitulo-06-glossario.md`                    | siglas e termos                                          |
| `capitulo-07-ferramentas.md`                  | ferramentas e limites                                    |
| `capitulo-08-resultados-solar.md`             | resultados por categoria                                 |
| `capitulo-09-classificacao-dos-resultados.md` | classificação contextual                                 |
| `capitulo-10-limitacoes.md`                   | limitações e pendências                                  |
| `capitulo-11-roteiro-pratico.md`              | reprodução e dois exemplos                               |
| `capitulo-12-conclusao-referencias.md`        | conclusão e referências                                  |

### Métricas e análises cobertas

Fan-in (Ca), fan-out (Ce), instabilidade (I), CBO, LCOM1, LCOM4, LCOM\*, TCC, complexidade ciclomática, complexidade cognitiva, LOC, SLOC, LLOC, tamanho de função, Long File, NOM, NOC, Halstead, MI, grafos, SCC, ciclos, alcançabilidade estática e em runtime, ramos, aninhamento, reprodutibilidade, determinismo, auditoria do relatório original, tracing de importações e `ProjectValidator`.

### Siglas

Todas as siglas usadas nos capítulos estão no [Capítulo 6](capitulo-06-glossario.md), com expansão, nome original e significado. As siglas que não têm expansão documentada no repositório foram marcadas como tal.

### Fontes

As referências conceituais e de ferramentas estão no [Capítulo 12](capitulo-12-conclusao-referencias.md), separadas das fontes específicas do SOLAR. Nenhuma URL foi inventada.

### Verificações executadas

| Verificação                                                                     | Resultado                                                               |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Links relativos entre capítulos e documentos                                    | todos resolvem para arquivos existentes                                 |
| Números de corpus (269/208/61/6.265/5.529)                                      | conferidos em `resumo_metricas.json`                                    |
| CC (553/1.278/2,31/2/5/10; A 523/B 30)                                          | conferida em `resumo_metricas.json` e CSV                               |
| Cognitiva (300/794/2,65/2/6/18)                                                 | conferida em CSV e auditoria                                            |
| Tamanho (13/16,6/35/163; 76/12/2)                                               | conferido em CSV                                                        |
| Halstead (291/553; 52,62%)                                                      | conferido em `resumo_metricas.json`                                     |
| MI (110/208; 32,26; Δ 47,62)                                                    | conferido em `resumo_metricas.json`                                     |
| Acoplamento (Ca 38; Ce 49; 70/107 zeros; I 60 indefinidos)                      | conferido em `modulos_acoplamento.csv`                                  |
| CBO (136/1,54/1/3/15)                                                           | conferido em `classes_cbo.csv`                                          |
| LCOM (39; LCOM1 3/10,82/28/89; LCOM4 1,13/3; TCC 0,30/0,398; LCOM\* 0,75/0,651) | conferido em `coesao_classes.csv`                                       |
| Ciclos (0 estáticos; 1 dinâmico; 207 SCCs)                                      | conferido em `resumo_metricas.json`                                     |
| Alcançabilidade (134/208; 14/625)                                               | conferido em `alcancabilidade.json` e `comparacao_alcancabilidade.json` |
| Alertas (60; 7/7/43/1/2)                                                        | conferido em `alertas_estruturais_revisados.csv`                        |
| Ramos (22/35) e aninhamento (2/35)                                              | conferido em `alertas_estruturais_revisados.csv`                        |
| Código de produção                                                              | **não alterado**                                                        |
| Relatórios originais                                                            | **não substituídos**                                                    |

### Lacunas e pendências declaradas

1. CBO absoluto com resolução de tipos não foi medido.
2. Complexidade cognitiva oficial do Sonar não foi executada.
3. Halstead por função está incompleto nesta implementação do Radon.
4. O MI não tem poder de discriminação nesta base.
5. Não há série histórica; não há medida de tendência.
6. Cobertura e eficácia dos testes não foram medidas.
7. O tracing de runtime não cobre rotas HTTP completas.
8. A eficácia das 29 regras não foi testada com defeitos injetados.
9. `SOLAR-ROF-003` não tem scanner no `ProjectValidator`; é implementada e tem teste unitário.

**Nenhuma dessas lacunas foi apresentada como resultado concluído.**
