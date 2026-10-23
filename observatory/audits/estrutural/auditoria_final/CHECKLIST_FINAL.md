# CHECKLIST FINAL — Etapas 2 e 3

**Data:** 22/10/2026
**Base:** commit `1b39b8e`; artefatos em `observatory/audits/estrutural/`; verificação independente em `observatory/audits/estrutural/auditoria_final/verificacoes.json`.
**Critério de status:**

- **VALIDADO** — há evidência verificada e recalculada de forma independente.
- **VALIDADO COM RESSALVAS** — o resultado é útil e reproduzível, mas há limitação metodológica declarada que impede conclusão absoluta.
- **PENDENTE** — falta evidência ou verificação necessária.
- **NÃO APLICÁVEL** — a métrica não tem domínio válido ou não mede o que se pretende neste corpus.

---

## Etapa 2 — Acoplamento e coesão

| #     | Item                                                              | Status                     | Evidência                                                                                                                                                                      | Arquivo / elemento                                                             | Justificativa técnica                                                                                                       | Ação                                                            |
| ----- | ----------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| E2-01 | Corpus de produção e exclusões                                    | **VALIDADO**               | `V1`: 208 arquivos, 136 classes; 0 erros de sintaxe                                                                                                                            | `modulos_metricas.csv`; `solar_metrics.py`                                     | Exclusões declaradas (`tests`, `docs`, `docker`, `reports`, `htmlcov`, `storage/` raiz); pacote `nucleus/storage/` incluído | Nenhuma                                                         |
| E2-02 | Fan-out (Ce) por módulo                                           | **VALIDADO**               | `V7`: 4 módulos conferidos; 3 idênticos, 1 explicado por arestas dinâmicas                                                                                                     | `solar_acoplamento_modulos.csv`                                                | Ce = módulos internos distintos importados; 0 imports não resolvidos                                                        | Nenhuma                                                         |
| E2-03 | Fan-in (Ca) por módulo                                            | **VALIDADO**               | `V7`; Ca de `solar_exception` = 0 (é folha) e de `project_validator` = 2                                                                                                       | `solar_acoplamento_modulos.csv`                                                | Ca considera somente produção; testes em coluna separada                                                                    | Nenhuma                                                         |
| E2-04 | Fan-in/fan-out do relatório original (mistura de testes/externos) | **VALIDADO COM RESSALVAS** | `rule` 33 = 32+1 teste; `source_files` 18 = 17+1; `kernel` 18 = 16+2 externos; `project_validator` 51 = 49+2                                                                   | `alertas_estruturais_revisados.csv`                                            | Valores reproduzidos, mas a métrica original mistura populações; `solar_exception` 57 não reproduz (38+25=63)               | Registrar a limitação; não reexecutar sem a ferramenta original |
| E2-05 | Instabilidade (`I = Ce/(Ca+Ce)`)                                  | **VALIDADO**               | Aritmética sobre Ca/Ce validados; 60 módulos com I indefinida                                                                                                                  | `resumo_metricas.json` → `coupling`                                            | Indefinição tratada como vazio, não zero; I agregado por camada separado do I intra-camada                                  | Nenhuma                                                         |
| E2-06 | Grafo de dependências internas                                    | **VALIDADO COM RESSALVAS** | 306 arestas; 0 não resolvidas; 1 diferida (`kernel → orbits.routes`); tracing executado em 2 cenários                                                                          | `dependencias_internas.csv`; `matriz_camadas.csv`; `runtime_tracing/`          | AST + imports dinâmicos verificáveis; runtime confirma; sem requisições HTTP                                                | P2 executado em 22/10/2026                                      |
| E2-07 | Ciclos e componentes fortemente conexos                           | **VALIDADO COM RESSALVAS** | 0 ciclos estáticos; 1 ciclo dinâmico; runtime: `Database` seq 226, `importlib(models)` 683, `importlib(user_model)` 684, `orm` publicado; cenário C falha com `AttributeError` | `solar_ciclos_internos.json`; `runtime_tracing/imports_runtime_bootstrap.json` | Causalidade confirmada por pilha; ciclo é relação de módulos + dependência temporal                                         | Nenhuma (P2 executado)                                          |
| E2-08 | CBO por classe (aproximação AST)                                  | **VALIDADO COM RESSALVAS** | `V6`: 5 classes de maior CBO com conjuntos de alvos idênticos                                                                                                                  | `solar_cbo_classes_estimado.csv`                                               | Aproximação estática; não resolve tipos, fábricas, `getattr`; CBO externo heurístico                                        | P1 se CBO absoluto for exigido                                  |
| E2-09 | CBO absoluto/tipado                                               | **PENDENTE**               | Não há análise de tipos executada                                                                                                                                              | —                                                                              | mypy/Pyright não produzem CBO diretamente; exigiria resolução de tipos própria                                              | P1                                                              |
| E2-10 | Aplicabilidade do LCOM                                            | **VALIDADO**               | 39 aplicáveis; 97 N/A (54 + 42 + 1)                                                                                                                                            | `solar_cbo_coesao_validacao.csv`                                               | `a=0`, `m<2` ou nenhum método de instância usando estado → N/A                                                              | Nenhuma                                                         |
| E2-11 | LCOM1, LCOM4 e TCC                                                | **VALIDADO**               | `V5`: 39 classes, **0 divergências** em LCOM1 e LCOM4 com implementação independente                                                                                           | `coesao_classes.csv`                                                           | `__init__` fora do LCOM principal; variante com `__init__` publicada                                                        | Nenhuma                                                         |
| E2-12 | Auditoria do LCOM original                                        | **VALIDADO**               | 3 falsos positivos provados (`Database` 15, `Storage` 15, `DatabaseDriver` 21); 1 parcial; 1 não reproduzível                                                                  | `alertas_estruturais_revisados.csv`                                            | Classes sem estado de instância produzem `C(m,2)` por construção                                                            | Nenhuma                                                         |
| E2-13 | Distribuição por camada/subcamada                                 | **VALIDADO**               | Matriz soma 306; intra 276 (90,2%), cross 30; I entre camadas distinto do I agregado                                                                                           | `camadas_consolidado.csv`; `subcamadas_resumo.csv`; `matriz_camadas.csv`       | `I` agregado inclui arestas intra-camada; o valor arquitetural é o cruzado                                                  | Nenhuma                                                         |
| E2-14 | Alcançabilidade                                                   | **VALIDADO COM RESSALVAS** | 134/208 estáticos; runtime: 14 confirmados ausentes (625 SLOC, 9,98%); `observatory.records` alcançável; 42 pacotes-pai implícitos                                             | `alcancabilidade.json`; `runtime_tracing/comparacao_alcancabilidade.json`      | Caminhos alternativos investigados e runtime executado; sem requisições HTTP                                                | P2 executado; ampliar cenários se exigido                       |
| E2-15 | Acoplamento em runtime                                            | **VALIDADO COM RESSALVAS** | 3 cenários executados (verificador, bootstrap, modelo isolado); 175 módulos SOLAR observados; 14 ausentes confirmados; 42 pacotes-pai implícitos                               | `runtime_tracing/RELATORIO_RUNTIME_TRACING.md`                                 | Dois caminhos de execução; sem requisições HTTP; `importlib` coberto por wrapper                                            | Ampliar para request-time se exigido                            |

**Resumo Etapa 2:** 8 VALIDADOS · 6 VALIDADOS COM RESSALVAS · 1 PENDENTE · 0 NÃO APLICÁVEIS.

---

## Etapa 3 — Complexidade

| #     | Item                                     | Status                     | Evidência                                                                | Arquivo / elemento                                  | Justificativa técnica                                                              | Ação                                 |
| ----- | ---------------------------------------- | -------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------ |
| E3-01 | Complexidade ciclomática                 | **VALIDADO**               | `V2`: 553 funções, soma 1.278, máx. 10                                   | `funcoes_complexidade.csv`                          | API do Radon com contagem própria; sem duplicação de métodos                       | Nenhuma                              |
| E3-02 | Distribuição de ranks e limiares         | **VALIDADO COM RESSALVAS** | 523 A / 30 B; nenhum ≥ 11                                                | `funcoes_complexidade.csv`                          | Ranks A–F são padrões do Radon, não limites universais                             | Declarar a origem dos limiares       |
| E3-03 | Tamanho de funções                       | **VALIDADO**               | `V2`: máx. 163 linhas; 76 > 30, 12 > 50, 2 > 100                         | `funcoes_complexidade.csv`                          | `endline − lineno + 1` (linhas físicas)                                            | Nenhuma                              |
| E3-04 | Tamanho de módulos (LOC/SLOC/LLOC)       | **VALIDADO**               | `tamanho.json` reproduzido 269/269                                       | `modulos_metricas.csv`                              | Valores do Radon `raw`; sem métrica caseira                                        | Nenhuma                              |
| E3-05 | Complexidade cognitiva                   | **VALIDADO COM RESSALVAS** | `V8`: 300 funções, soma 794, máx. 18, mesmos top 5                       | `complexidade_cognitiva.csv`                        | Plugin “sonar-like”, não Sonar oficial; comparável apenas dentro do projeto        | P3 se comparação externa for exigida |
| E3-06 | Limiar de 15                             | **VALIDADO COM RESSALVAS** | 1 função acima de 15 (`_destination`, 18)                                | `complexidade_cognitiva.csv`                        | 15 é default da regra S3776 do Sonar, não limite universal                         | Declarar a origem                    |
| E3-07 | Sonar oficial                            | **PENDENTE**               | Não executado                                                            | —                                                   | Ferramenta não disponível no ambiente                                              | P3                                   |
| E3-08 | Halstead por módulo                      | **VALIDADO COM RESSALVAS** | `halstead.json` reproduzido 269/269; volume produção 6.094,74            | `radon_halstead_modulos.csv`                        | Volume é limite inferior (não conta chamadas)                                      | P2 se Halstead for evidência         |
| E3-09 | Halstead por função                      | **NÃO APLICÁVEL**          | 291/553 (52,62%) com `N1=N2=0` na produção; 561/1.233 (45,50%) no corpus | `verificacoes.json` → V3                            | Visitante do Radon não implementa `visit_Call`/`visit_Subscript`; mede outra coisa | Substituir se necessário (P2)        |
| E3-10 | Contagem de funções e proporção de zeros | **VALIDADO COM RESSALVAS** | API 1.233/561; JSON 1.219/548; 14 homônimos perdidos                     | `verificacoes.json` → V3; `nucleus/rules/report.py` | JSON do CLI usa dicionário por nome; produção é 291/553                            | Usar a API para contagens por função |
| E3-11 | Reprodutibilidade do MI                  | **VALIDADO**               | 269/269 idênticos (diff 0,0)                                             | `validacao_radon.json`                              | Fórmula do Radon confirmada no código-fonte                                        | Nenhuma                              |
| E3-12 | MI como discriminador                    | **NÃO APLICÁVEL**          | 110/208 (52,9%) com MI=100 por `V=0`; mínimo 32,26 em arquivo de 15 SLOC | `modulos_metricas.csv`                              | Saturação e termo de comentários impedem uso comparativo                           | P5 (política)                        |
| E3-13 | Sensibilidade do MI a docstrings         | **VALIDADO**               | 26 módulos > 10 pontos; delta máx. +47,62; mínimo 50,35                  | `modulos_metricas.csv` (`mi_sem_multiline`)         | `count_multi` altera o resultado materialmente                                     | P5                                   |
| E3-14 | Reprodutibilidade dos relatórios Radon   | **VALIDADO**               | 0 divergências em CC (208), Halstead/raw/MI (269)                        | `validacao_radon.json`                              | Execução com Radon 6.0.1 e API oficial                                             | Nenhuma                              |
| E3-15 | Determinismo dos scripts próprios        | **VALIDADO**               | Hashes idênticos em duas execuções                                       | `solar_metrics.py`; `revisar_relatorio.py`          | Correção de ordenação de empates                                                   | Nenhuma                              |
| E3-16 | Evolução histórica                       | **NÃO APLICÁVEL**          | Uma única fotografia                                                     | —                                                   | Fora do escopo das Etapas 2/3                                                      | —                                    |

**Resumo Etapa 3:** 6 VALIDADOS · 5 VALIDADOS COM RESSALVAS · 1 PENDENTE · 3 NÃO APLICÁVEIS.

---

## Correções efetuadas durante a auditoria

| #   | Correção                                                                     | Onde                                               | Impacto                                                                                                |
| --- | ---------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| C1  | Ordenação determinística de rankings (`top_Ce`, `top_Ca`, `top_instability`) | `solar_metrics.py`                                 | Reprodutibilidade byte a byte; nenhum valor numérico mudou                                             |
| C2  | Explicação dos 61 arquivos sem blocos de CC                                  | `RELATORIO_CONSOLIDADO.md` §1.1/§2.2               | Corrige “61 `__init__.py` vazios” para 59 inits sem código + 1 init com reexportações + 1 módulo vazio |
| C3  | Inits sem arestas                                                            | `RELATORIO_CONSOLIDADO.md` §7.2                    | 58 sem arestas; 1 com Ca=1 (import dinâmico)                                                           |
| C4  | Categorias de coesão                                                         | `RELATORIO_CONSOLIDADO.md` §8.2                    | 39/50/33/4/4/6 (antes 41/49/33/9/3/1)                                                                  |
| C5  | Contagens e proporções de Halstead                                           | `RELATORIO_CONSOLIDADO.md` §5, §0, §11, pendências | 1.233/561/45,50% (API), 1.219/548/44,95% (JSON), 291/553/52,62% (produção); 14 homônimos perdidos      |

**Nenhum arquivo de `nucleus/`, `orbits/`, `observatory/`, `tests/` ou `reports/quality/` foi alterado.**

---

## O que já está validado

- Fan-in, fan-out, instabilidade e distribuição por camada (com definições explícitas e testes de consistência).
- Grafo interno de 306 arestas, com 0 imports não resolvidos.
- Ciclos: 0 estáticos, 1 dinâmico, com evidência de linha e de runtime.
- LCOM1/LCOM4/TCC nas 39 classes aplicáveis (0 divergências contra implementação independente).
- CC (553/1.278/10), tamanho de funções e módulos.
- Reprodutibilidade integral dos quatro JSONs Radon e da complexidade cognitiva.
- Determinismo dos scripts de análise após C1.

## O que está validado com ressalvas

- CBO (aproximação AST; 5 casos conferidos, sem resolução de tipos).
- Complexidade cognitiva (plugin “sonar-like”).
- Halstead por módulo (limite inferior) e contagens por função (colisões de nomes no JSON).
- Alcançabilidade e acoplamento em runtime (3 cenários; 14 ausentes confirmados; 42 pacotes-pai implícitos; sem requisições HTTP).
- Metas de fan-in do relatório original (mistura de testes/externos; 1 valor histórico não reproduzível).

## O que ainda está pendente

- CBO absoluto/tipado (P1).
- Sonar oficial (P3), se exigido.
- Halstead completo (P4), se exigido.
- Ampliação do tracing para request-time e outros pontos de entrada, se exigido.
- Política formal do MI (P5), decisão documental.
