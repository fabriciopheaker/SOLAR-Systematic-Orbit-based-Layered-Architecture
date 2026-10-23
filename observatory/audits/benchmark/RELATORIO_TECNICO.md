# Relatório técnico — viabilidade do benchmark comparativo

**Projeto:** SOLAR
**Data:** 2026-10-23
**Status:** estudo de viabilidade; **nenhuma execução comparativa**
**Código de produção alterado:** não

---

## 1. Objetivo

Avaliar se é possível produzir, agora, um benchmark empírico e reproduzível
comparando SOLAR, Clean Architecture, MVC e Hexagonal; e, se não for, entregar
o plano e a análise de viabilidade sem inventar resultados.

---

## 2. Inventário do que existe

| Ativo                               | Existe?     | Onde/observação                              |
| ----------------------------------- | ----------- | -------------------------------------------- |
| Implementação SOLAR                 | **sim**     | `nucleus/`, `orbits/`, `observatory/`        |
| Implementação Clean equivalente     | **não**     | não há no repositório                        |
| Implementação MVC equivalente       | **não**     | não há no repositório                        |
| Implementação Hexagonal equivalente | **não**     | não há no repositório                        |
| Especificação funcional congelada   | **não**     | o Planet `example` é uma referência parcial  |
| Testes de aceitação comuns          | **não**     | a suíte testa a SOLAR, não um contrato comum |
| Harness de carga                    | **parcial** | etapa 4, específico da SOLAR                 |
| Dados de carga da SOLAR             | **sim**     | etapa 4                                      |
| Ambiente controlado                 | **parcial** | uma máquina, uma execução                    |
| Requisitos de desempenho            | **não**     | nenhum SLO formal                            |
| Pool de mantenedores                | **não**     | nenhum estudo humano                         |
| Série histórica                     | **não**     | uma fotografia                               |
| Orçamento/pessoas                   | **não**     | não informado                                |

---

## 3. Análise de viabilidade

### 3.1 O que é viável agora

1. **Benchmark interno da SOLAR:** repetir a etapa 4 em ambiente controlado,
   com mais repetições, SLOs e comparação antes/depois de correções. Isso mede
   a SOLAR, não compara arquiteturas.
2. **Benchmark estrutural descritivo:** comparar métricas estáticas da SOLAR
   com valores publicados de outras arquiteturas, **desde que** o corpus, a
   linguagem e as definições sejam equivalentes. Hoje não são.
3. **Plano experimental completo:** este documento.

### 3.2 O que não é viável agora

| Bloqueio                               | Consequência                                        |
| -------------------------------------- | --------------------------------------------------- |
| Falta de 3 implementações equivalentes | qualquer comparação seria entre sistemas diferentes |
| Falta de especificação congelada       | funcionalidades e escopos divergiriam               |
| Falta de harness comum                 | latência/vazão não seriam comparáveis               |
| Falta de ambiente controlado           | variabilidade externa dominaria o efeito            |
| Falta de SLO                           | não haveria critério de “melhor”                    |
| Falta de estudo humano                 | manutenibilidade seria opinião                      |
| Falta de orçamento/pessoas             | 8–12 semanas e 2–3 pessoas não estão alocadas       |

### 3.3 O que seria fabricação

- preencher uma tabela com latências “esperadas”;
- comparar a SOLAR com um MVC hipotético descrito em artigo;
- usar métricas de projetos open source de portes diferentes como se fossem
  equivalentes;
- atribuir diferença de desempenho ao estilo arquitetural sem controlar
  implementação, hash, banco e hardware;
- apresentar MI como medida de manutenibilidade;
- usar uma única execução como resultado.

Nenhuma dessas práticas foi adotada.

---

## 4. Desenho proposto (resumo)

O detalhamento está em [`PLANO_DE_BENCHMARK.md`](PLANO_DE_BENCHMARK.md).

| Elemento       | Definição                                                 |
| -------------- | --------------------------------------------------------- |
| Sistema        | 8 funcionalidades comuns (health, CRUD, login, upload)    |
| Implementações | SOLAR, Clean, MVC, Hexagonal                              |
| Stack          | mesma versão de Python/Flask/SQLAlchemy/bcrypt            |
| Carga          | c1, c2, c4, c8, c16; ≥ 5 repetições                       |
| Desempenho     | P50/P95/P99, vazão, erro, CPU, memória, startup           |
| Estrutura      | Ce/Ca, ciclos, CBO, LCOM, CC, cognitiva, MI descritivo    |
| Evolução       | M1–M8, tempo, arquivos, retrabalho, defeitos              |
| Testes         | cobertura, mutação, flakiness                             |
| Humano         | ≥ 5 participantes por arquitetura                         |
| Análise        | bootstrap, Mann-Whitney/Kruskal-Wallis, tamanho de efeito |
| Validade       | testes de aceitação comuns, ambiente único, dados brutos  |

---

## 5. O que já pode ser dito com os dados atuais

Estas afirmações são **sobre a SOLAR**, não comparativas:

| Afirmação                              | Evidência                                   |
| -------------------------------------- | ------------------------------------------- |
| A SOLAR tem baixo acoplamento interno  | 306 arestas / 208 módulos; densidade 0,71%  |
| A SOLAR tem 0 ciclos estáticos         | Tarjan no grafo AST                         |
| A SOLAR tem 1 ciclo dinâmico           | `Database ↔ user_model`                     |
| A complexidade de controle é baixa     | CC mediana 2; 94,6% rank A                  |
| Há um gargalo de escrita concorrente   | etapa 4: 30% de erro em c4                  |
| Há riscos de segurança não confirmados | etapa 5: endpoint público, sem tipo/tamanho |
| A manutenibilidade não foi demonstrada | etapa 6: MI saturado; sem estudo humano     |

**Nenhuma dessas linhas autoriza dizer que a SOLAR é melhor ou pior que Clean,
MVC ou Hexagonal.**

---

## 6. Riscos do projeto de benchmark

| Risco                           | Probabilidade | Impacto | Mitigação                           |
| ------------------------------- | ------------- | ------- | ----------------------------------- |
| Viés do autor da SOLAR          | alta          | alto    | avaliador independente              |
| Implementações não equivalentes | alta          | alto    | testes de aceitação comuns          |
| Variabilidade do ambiente       | média         | alto    | mesmo host/container; randomização  |
| Amostra pequena                 | média         | médio   | ≥ 5 repetições; IC                  |
| Tarefas favorecem um estilo     | média         | alto    | 8 cenários; revisão por pares       |
| MI saturado                     | alta          | médio   | não usar como desfecho principal    |
| Prazo/custo                     | alta          | alto    | fase 0 antes de prometer resultados |
| Publicação seletiva             | média         | médio   | pré-registro do plano               |

---

## 7. Cronograma e esforço

| Fase              | Duração          | Entregável                        |
| ----------------- | ---------------- | --------------------------------- |
| 0 — Preparação    | 2–3 semanas      | 4 implementações + harness + spec |
| 1 — Piloto        | 1 semana         | variabilidade e tamanho amostral  |
| 2 — Execução      | 2–3 semanas      | dados brutos de carga             |
| 3 — Estudo humano | 2–3 semanas      | dados de compreensão              |
| 4 — Análise       | 1–2 semanas      | relatório + pacote                |
| **Total**         | **8–12 semanas** | **2–3 pessoas**                   |

Sem essa alocação, o benchmark não passa de intenção.

---

## 8. Conclusão de viabilidade

| Pergunta                                         | Resposta                                     |
| ------------------------------------------------ | -------------------------------------------- |
| É possível comparar as quatro arquiteturas hoje? | **não**                                      |
| É possível entregar um plano reproduzível?       | **sim** (este diretório)                     |
| É possível entregar resultados sem fabricar?     | **não**                                      |
| O que falta primeiro?                            | implementações equivalentes + spec + harness |
| Qual é o próximo passo?                          | fase 0 do plano                              |

**Veredito:** o benchmark é **viável como projeto**, não como resultado
imediato. A entrega correta agora é o plano e a análise de viabilidade. A
entrega de números comparativos fica condicionada à execução da fase 0.
