# Capítulo 12 — Conclusão e referências

> **Pergunta deste capítulo:** o que se pode afirmar, com segurança, sobre a arquitetura do SOLAR?

---

## 12.1 O que foi feito

Esta documentação percorreu quatro movimentos:

1. **Conceitos:** arquitetura, qualidade, módulo, classe, função, dependência, acoplamento, coesão, complexidade, manutenibilidade e evolução.
2. **Método:** análise estática, tracing de runtime, grafo, métricas, inspeção manual, testes e validação independente.
3. **Resultados:** 269 arquivos, 208 módulos de produção, 6.261 SLOC, 136 classes, 553 funções, 306 arestas.
4. **Leitura:** classificação contextual, limitações e roteiro de reprodução.

O objetivo não foi “dar uma nota” à arquitetura, mas tornar as conclusões **verificáveis, delimitadas e discutíveis**.

---

## 12.2 O que os dados sustentam

| Afirmação                                               | Evidência                                                           | Grau de confiança                             |
| ------------------------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------- |
| O código de produção é pequeno e concentrado no Nucleus | 6.261 SLOC; 63% no `nucleus/rules`                                  | alto                                          |
| O acoplamento interno é baixo e esparso                 | Ce mediano 3; densidade 0,71%; 90,2% intra-camada                   | alto                                          |
| Os hubs de acoplamento têm papel arquitetural           | `solar_exception` Ca 38; `project_validator` Ce 49; `Kernel` CBO 15 | alto                                          |
| A complexidade de controle é baixa na maior parte       | CC mediana 2; 94,6% rank A                                          | alto                                          |
| A complexidade cognitiva se concentra em scanners       | 752 de 794 pontos no Nucleus                                        | alto                                          |
| Há um outlier de legibilidade                           | `_destination`: CC 10, cognitiva 18                                 | alto                                          |
| O tamanho é dominado por funções curtas                 | mediana 13 linhas; 76 > 30                                          | alto                                          |
| Há um ciclo dinâmico com dependência de ordem           | `Database ↔ user_model`; 3 cenários                                 | alto                                          |
| Há 14 módulos não exercitados                           | 625 SLOC; 9,98% da produção                                         | alto para os cenários; incerto para o sistema |
| O MI não discrimina                                     | 110 de 208 módulos com MI 100                                       | alto                                          |
| Halstead está incompleto nesta implementação            | 52,62% das funções com `n1 = n2 = 0`                                | alto                                          |
| A coesão de estado é baixa em parte das classes         | LCOM\* mediano 0,75; TCC mediano 0,30                               | médio (depende do papel)                      |
| A conformidade arquitetural é parcial                   | 29 regras executadas; ROF-003 sem scanner                           | alto                                          |

---

## 12.3 O que os dados **não** sustentam

| Afirmação tentadora               | Por que não se sustenta                                       |
| --------------------------------- | ------------------------------------------------------------- |
| “A arquitetura é boa.”            | Nenhuma métrica mede qualidade global; não há critério único. |
| “O código é fácil de manter.”     | MI saturado; não há estudo com mantenedores.                  |
| “Os 14 módulos são código morto.” | Ausência em 3 cenários não prova desuso.                      |
| “O ciclo causa falhas.”           | Não houve falha observada; há dependência de ordem.           |
| “A coesão é ruim.”                | 39 classes têm domínio; 97 são N/A; LCOM1 cresce com métodos. |
| “O projeto está 100% conforme.”   | ROF-003 não é executada.                                      |
| “A dívida está aumentando.”       | Há uma única fotografia.                                      |
| “O desempenho é bom.”             | Não há benchmarks.                                            |
| “Os testes cobrem o sistema.”     | Cobertura e eficácia não foram medidas.                       |

---

## 12.4 Síntese arquitetural

O SOLAR apresenta uma estrutura **coerente com o estilo que declara**:

- o Nucleus concentra regras, contratos e scanners;
- a Atmosphere trata requisições;
- os Orbits compõem e persistem;
- os Planets são módulos funcionais;
- o Observatory verifica;
- o Bootstrap monta.

Os números compatíveis com essa leitura:

- 90,2% das arestas ficam dentro da camada;
- os maiores fan-in/fan-out pertencem a contratos, composição e registro de regras;
- a complexidade cognitiva se concentra no Nucleus, onde estão as decisões;
- não há ciclo estático;
- o validador passa nas 29 regras ativas.

Os achados que merecem atenção:

1. **14 módulos não exercitados** (segurança de borda e upload): funcionalidade possivelmente não conectada.
2. **Ciclo `Database ↔ user_model`**: dependência de ordem de inicialização; risco de erro pouco explícito.
3. **`_destination`**: maior CC e maior cognitiva; único acima de 15.
4. **`Kernel.mount`**: 163 linhas; longo e linear, mas concentra a composição.
5. **MI e Halstead**: não usáveis como ranking; servem como alerta de método.
6. **ROF-003**: regra sem scanner; conformidade parcial.

Nenhum desses achados é, por si, um defeito. São **lugares para ler primeiro**.

---

## 12.5 O que fazer a seguir

| Prioridade | Ação                                                               | Por quê                     | Não fazer                         |
| ---------- | ------------------------------------------------------------------ | --------------------------- | --------------------------------- |
| 1          | Decidir o destino dos 14 módulos (conectar, documentar ou remover) | impacto funcional/segurança | remover por métrica               |
| 2          | Documentar a ordem de inicialização do ciclo                       | risco de erro               | “corrigir” sem entender           |
| 3          | Inspecionar `_destination` e `Kernel.mount`                        | legibilidade/teste          | refatorar por número              |
| 4          | Implementar o scanner da ROF-003                                   | conformidade real           | declarar conformidade total       |
| 5          | Recolher linha de base histórica                                   | medir tendência             | comparar com limites universais   |
| 6          | Medir cobertura de testes                                          | saber o que é testado       | confundir cobertura com qualidade |
| 7          | Rodar Sonar oficial, se necessário                                 | comparar cognitiva          | tratar plugin como oficial        |

**Regra:** nenhuma ação deve ser executada apenas porque uma métrica passou de um limite. A ação precisa de hipótese, evidência e critério de sucesso.

---

## 12.6 O que esta documentação é e não é

| É                                        | Não é                      |
| ---------------------------------------- | -------------------------- |
| um guia didático de análise arquitetural | um laudo de qualidade      |
| uma auditoria reproduzível               | uma certificação           |
| uma leitura contextual dos números       | uma lista de defeitos      |
| um registro de limitações                | uma promessa de completude |
| uma base para decisões                   | uma decisão tomada         |

---

## 12.7 Referências conceituais

As referências abaixo fundamentam os conceitos e as fórmulas. Não são fontes dos números do SOLAR; os números vêm dos artefatos do projeto.

1. **PARNAS, D. L.** On the Criteria To Be Used in Decomposing Systems into Modules. _Communications of the ACM_, v. 15, n. 12, p. 1053–1058, 1972.
2. **McCABE, T. J.** A Complexity Measure. _IEEE Transactions on Software Engineering_, v. SE-2, n. 4, p. 308–320, 1976.
3. **HALSTEAD, M. H.** _Elements of Software Science_. New York: Elsevier North-Holland, 1977.
4. **YOURDON, E.; CONSTANTINE, L. L.** _Structured Design: Fundamentals of a Discipline of Computer Program and Systems Design_. Englewood Cliffs: Prentice Hall, 1979.
5. **CHIDAMBER, S. R.; KEMERER, C. F.** A Metrics Suite for Object Oriented Design. _IEEE Transactions on Software Engineering_, v. 20, n. 6, p. 476–493, 1994.
6. **COLEMAN, D.; ASH, D.; LOWTHER, B.; OMAN, P.** Using Metrics to Evaluate Software System Maintainability. _IEEE Computer_, v. 27, n. 8, p. 44–49, 1994.
7. **HITZ, M.; MONTAZERI, B.** Measuring Coupling and Cohesion in Object-Oriented Systems. In: _Proceedings of the International Symposium on Applied Corporate Computing_, 1995.
8. **HENDERSON-SELLERS, B.** _Object-Oriented Metrics: Measures of Complexity_. Upper Saddle River: Prentice Hall, 1996.
9. **FENTON, N. E.; PFLEEGER, S. L.** _Software Metrics: A Rigorous and Practical Approach_. 2. ed. London: PWS Publishing, 1997.
10. **MARTIN, R. C.** _Agile Software Development: Principles, Patterns, and Practices_. Upper Saddle River: Prentice Hall, 2003. (instabilidade e dependências)
11. **ISO/IEC 25010** — _Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models_. 2011; revisão de 2023.
12. **SONARSOURCE.** _Cognitive Complexity: A New Way to Measure the Understandability of Code_. Whitepaper técnico. (origem conceitual da complexidade cognitiva e da regra S3776)

---

## 12.8 Referências de ferramentas

1. **RADON** — ferramenta Python de métricas de código, versão 6.0.1. Documentação e código-fonte do projeto Radon. (CC, Halstead, MI e `raw`)
2. **FLAKE8** — ferramenta de lint para Python, versão 7.4.1. Documentação oficial.
3. **FLAKE8-COGNITIVE-COMPLEXITY** — plugin de complexidade cognitiva, versão 0.1.0, publicado no PyPI.
4. **PYTHON SOFTWARE FOUNDATION.** Documentação do Python 3.14: módulos `ast`, `sys` (incluindo `sys.addaudithook`) e `importlib`.
5. **SONARQUBE** — regra S3776 (_Cognitive Complexity of functions should not be too high_), documentação da plataforma SonarQube.

**Observação:** as referências são citadas por autor, obra e ano; não foram inventados URLs. Quando a documentação de uma ferramenta é citada, o nome e a versão identificam a fonte.

---

## 12.9 Referências específicas do SOLAR

| Documento                                                                                                                                                                                        | Conteúdo                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| [`docs/manual.md`](../manual.md)                                                                                                                                                                 | manual arquitetural do SOLAR; regras, camadas e fluxo |
| [`docs/rules.md`](../rules.md)                                                                                                                                                                   | catálogo das 30 regras e códigos `RED`, `ROF`, `SEG`  |
| [`observatory/audits/estrutural/RELATORIO_CONSOLIDADO.md`](../../observatory/audits/estrutural/RELATORIO_CONSOLIDADO.md)                                                                         | relatório consolidado da análise                      |
| [`observatory/audits/estrutural/resumo_metricas.json`](../../observatory/audits/estrutural/resumo_metricas.json)                                                                                 | resumo quantitativo                                   |
| [`observatory/audits/estrutural/alertas_estruturais_revisados.csv`](../../observatory/audits/estrutural/alertas_estruturais_revisados.csv)                                                       | auditoria dos 60 alertas                              |
| [`observatory/audits/estrutural/auditoria_final/AUDITORIA_ETAPA_2.md`](../../observatory/audits/estrutural/auditoria_final/AUDITORIA_ETAPA_2.md)                                                 | auditoria de acoplamento/coesão                       |
| [`observatory/audits/estrutural/auditoria_final/AUDITORIA_ETAPA_3.md`](../../observatory/audits/estrutural/auditoria_final/AUDITORIA_ETAPA_3.md)                                                 | auditoria de complexidade                             |
| [`observatory/audits/estrutural/auditoria_final/runtime_tracing/RELATORIO_RUNTIME_TRACING.md`](../../observatory/audits/estrutural/auditoria_final/runtime_tracing/RELATORIO_RUNTIME_TRACING.md) | tracing de importações                                |
| [`docs/analise-arquitetural/DOCUMENTACAO_ANALISE_ARQUITETURAL.md`](DOCUMENTACAO_ANALISE_ARQUITETURAL.md)                                                                                         | índice desta documentação                             |

---

## 12.10 Conclusão

A análise do SOLAR não encontrou um sistema caótico. Encontrou um sistema **pequeno, estruturalmente coerente e com baixa complexidade de controle**, cujos maiores riscos não estão nos números altos de acoplamento — esses são explicados pelo papel dos componentes — mas em **pontos de conexão e cobertura**:

- capacidades implementadas que os cenários não exercitam;
- uma dependência de ordem de inicialização;
- um outlier de legibilidade;
- uma regra arquitetural sem scanner;
- métricas compostas que não discriminam.

A conclusão mais importante é metodológica: **um número sem escopo, método e contexto é apenas um número**. Com escopo, método e contexto, os números do SOLAR permitem decisões melhores — desde que ninguém confunda “não observado” com “inexistente”, “N/A” com “ruim” ou “MI 100” com “perfeito”.

---

## 12.11 Checklist final da documentação

- [x] Todos os capítulos de 1 a 12 criados.
- [x] Todas as métricas analisadas têm ficha com definição, fórmula, exemplo, resultado, limitações e status.
- [x] Todas as siglas usadas foram expandidas e estão no glossário.
- [x] Os números foram conferidos contra os artefatos de `observatory/audits/estrutural/`.
- [x] As aproximações foram declaradas.
- [x] As pendências foram declaradas.
- [x] Nenhum código de produção foi alterado.
- [x] Nenhum relatório original foi substituído.
- [x] Links relativos entre capítulos e documentos foram criados.

**Fim da documentação.**
