# PLANO DE AÇÃO — verificações restantes para encerrar as Etapas 2 e 3

> **Nota (2026-10-23):** documento histórico. Caminhos `observatory/audits/estrutural/`
> foram movidos para `etapa_2_acoplamento_coesao/` e `etapa_3_complexidade/`.

**Data:** 22/10/2026
**Premissa:** este plano contém **apenas** o que ainda falta para o encerramento formal. Tudo o que já foi validado (ver `CHECKLIST_FINAL.md`) não deve ser refeito.

**Duas formas de encerrar:**

- **Caminho documental (curto):** aceitar formalmente as limitações declaradas e registrar a decisão. Nenhuma execução nova é necessária além deste registro.
- **Caminho rigoroso:** executar as verificações condicionais abaixo antes de encerrar.

A escolha entre os caminhos é do avaliador; o plano marca o que cada uma destrava.

---

## 1. Prioridades

| Prioridade | Verificação                                     | Bloqueia                                           | Condição                                               | Esforço estimado        |
| ---------- | ----------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------ | ----------------------- |
| **P1**     | CBO com resolução de tipos                      | Etapa 2 (apenas se CBO absoluto for exigido)       | O protocolo exige CBO comparável a ferramentas tipadas | 2–4 h                   |
| **P2**     | Tracing de importação em runtime                | **Executada em 22/10/2026**                        | Resultado em `runtime_tracing/`; escopo parcial        | Concluída com ressalvas |
| **P3**     | Política formal do MI                           | Etapa 3 (documental)                               | Sempre que o MI for citado como métrica                | 15 min                  |
| **P4**     | Halstead com visitante completo                 | Etapa 3 (apenas se Halstead for evidência)         | O protocolo exige Halstead por função                  | 3–4 h                   |
| **P5**     | SonarQube/SonarCloud (S3776)                    | Etapa 3 (apenas se comparação externa for exigida) | O protocolo exige complexidade cognitiva oficial       | 1–2 h                   |
| **P6**     | Reproduzir a ferramenta original de code smells | Nenhuma das duas etapas                            | Só se o objeto de auditoria for o relatório original   | 4–8 h                   |

> **P6 não bloqueia as Etapas 2 e 3.** As divergências do relatório original (fan-in 57, NOC 127,6, “effective code lines”) já estão documentadas e isoladas em `alertas_estruturais_revisados.csv`.

---

## 2. P1 — CBO com resolução de tipos

**Por que é necessário:** o CBO publicado é uma aproximação por AST. Ele foi validado contra implementação independente (5 classes, alvos idênticos), mas **não resolve tipos**; portanto, não é comparável a CBO de ferramentas que fazem ligação de tipos (Java/C++) nem detecta acoplamento por injeção/fábrica/`getattr`.

**Se o protocolo aceitar a aproximação declarada:** nenhuma ação. Registrar em ata: “CBO medido por AST, validado por consistência interna, sem pretensão de comparação externa”.

**Se exigir CBO absoluto:**

1. Instalar um resolvedor de tipos: `py -m pip install pyright` (ou `mypy`).
2. Criar um script de CBO tipado:
   - resolver, para cada `Name`/`Attribute` no corpo da classe, o tipo declarado/inferido (via Pyright JSON ou `jedi`);
   - mapear o tipo para a classe qualificada do projeto;
   - contar classes distintas.
3. Comparar com `observatory/audits/estrutural/classes_cbo_estimado.csv`.
4. Publicar `classes_cbo_tipado.csv` e o delta.

**Critério de aceite:** para as 10 classes de maior CBO, o conjunto de alvos tipados deve ser igual ou superconjunto do conjunto AST; diferenças devem ser explicadas (ex.: `Database.orm` resolve para tipo externo).

**Artefato de saída:** `observatory/audits/estrutural/auditoria_final/cbo_tipado.csv` + nota metodológica.

---

## 3. P2 — Tracing de importação em runtime

**Por que é necessário:** o grafo cobre imports estáticos e o único padrão dinâmico verificável (`importlib.import_module` + `pkgutil.iter_modules`). Não há prova de que **nenhum outro** caminho dinâmico exista em execução (plugins, `getattr` em módulo, CLI, Flask).

**Status: EXECUTADA em 22/10/2026.** Resultados em `observatory/audits/estrutural/auditoria_final/runtime_tracing/`:

- três cenários (verificador, bootstrap com SQLite, modelo isolado), em processos separados;
- 175 módulos SOLAR observados na união; 14 dos 15 não alcançáveis confirmados ausentes;
- `observatory.records` **refutado** (carregado como pacote-pai) → correção 15 → 14, 625 SLOC (9,98%);
- 42 pacotes-pai implícitos observados fora do BFS estático (limitação do grafo, não da SOLAR);
- ciclo `Database ↔ user_model` confirmado por pilha (`database.py:167`) e por estado (`orm` publicado).

**Escopo restante (somente se exigido):** tracing de requisições HTTP e de outros pontos de entrada (jobs/CLI), para capturar imports preguiçosos em handlers e caminhos de erro.

**Procedimento utilizado (histórico):**

1. Criar um wrapper de instrumentação (fora do código da SOLAR) com `sys.addaudithook` para registrar eventos `import` durante:
   - o bootstrap (`Kernel().mount()` com configuração de teste/sqlite), e
   - uma execução do verificador (`python -m observatory.solar check`).
2. Registrar os módulos efetivamente importados em `sys.modules`.
3. Comparar com o conjunto de 134 módulos alcançáveis.
4. Verificar em runtime que `orbits.database.models.user_model` é importado por `Database.sync()` e que `nucleus.database.database` já está em `sys.modules` no momento do import (confirmação do ciclo).

**Critério de aceite:** **atingido com ressalva de escopo.** A união dos cenários cobre 175 módulos SOLAR; 132 dos 133 módulos alcançáveis com código foram observados (o único ausente é `observatory.solar.__main__`, não executado). Os 42 módulos fora do BFS foram todos classificados como pacotes-pai implícitos; nenhum ficou sem explicação.

**Artefatos produzidos:** `trace_imports.py`, `imports_runtime_verificador.json`, `imports_runtime_bootstrap.json`, `imports_runtime_modelo_isolado.json`, `comparacao_alcancabilidade.json`, `verificador_stdout.txt`, `check_audit/` e `RELATORIO_RUNTIME_TRACING.md`.

> Observação: o bootstrap usou SQLite em arquivo temporário (`DB_CONNECTION=sqlite`) e não subiu servidor. Não é um teste de carga nem de desempenho.

---

## 4. P3 — Política formal do MI (documental)

**Por que é necessário:** o MI publicado usa `count_multi=True` (docstrings contam como comentário). A sensibilidade mostra 26 módulos com variação > 10 pontos e máximo de +47,62. Sem uma política declarada, o número não é interpretável.

**Ação (sem execução):**

1. Escolher e registrar uma das políticas:
   - **(a)** reportar o MI do Radon como está, apenas como artefato, **sem uso em conclusões**; ou
   - **(b)** reportar as duas variantes (`mi` e `mi_sem_multiline`) e usar a mediana/rank apenas descritivamente; ou
   - **(c)** não reportar MI e justificar pela saturação (110/208 em 100).
2. Registrar a decisão em `AUDITORIA_ETAPA_3.md` (seção de metodologia).

**Critério de aceite:** a política escolhida está escrita e os números citados são coerentes com ela.

**Custo:** 15 minutos. **Impacto:** fecha a única pendência metodológica da Etapa 3 que não depende de ferramenta externa.

---

## 5. P4 — Halstead com visitante completo (condicional)

**Por que é necessário:** o visitante do Radon não conta `Call`, `Subscript` nem `Attribute` como operadores; 52,62% das funções de produção têm `N1=N2=0`. A métrica, como está, **não mede complexidade de expressão**.

**Se o protocolo aceitar o achado de não aplicabilidade:** nenhuma ação. O resultado “Halstead não é utilizável nesta base” já está sustentado por dados.

**Se Halstead for exigido como evidência:**

1. Implementar um visitante AST que conte operadores conforme a definição original de Halstead:
   - operadores: aritméticos, comparação, booleanos, atribuição aumentada, `Call`, `Attribute`, `Subscript`;
   - operandos: nomes, constantes, literais de coleção, resultados de chamada.
2. Validar contra um conjunto manual de 10 funções.
3. Publicar `halstead_completo.csv` com `h1,h2,N1,N2,V,D,E` por função.
4. Comparar com o Radon e registrar o delta.

**Critério de aceite:** 0 funções com `N1=N2=0` sem justificativa (funções vazias); volume por função > 0 para toda função com corpo.

**Artefato de saída:** `observatory/audits/estrutural/auditoria_final/halstead_completo.csv` + metodologia.

---

## 6. P5 — SonarQube/SonarCloud (condicional)

**Por que é necessário:** a complexidade cognitiva vem de um plugin “sonar-like”; não é o Sonar oficial. Se o protocolo exigir comparação com a literatura/Sonar, é preciso rodar a ferramenta oficial.

**Como executar:**

- SonarCloud (projeto público) ou SonarQube Community via Docker (o ambiente Docker está no WSL; não há CLI Docker no Windows — ver memória do repositório);
- analisar `nucleus/`, `orbits/`, `observatory/`, `server.py`;
- extrair a regra **S3776** (Cognitive Complexity) por função.

**Critério de aceite:** ranking das 10 funções de maior complexidade cognitiva; comparação com `complexidade_cognitiva.csv`; divergências explicadas pela diferença de especificação.

**Artefato de saída:** `observatory/audits/estrutural/auditoria_final/sonar_s3776.csv`.

---

## 7. P6 — Ferramenta original de code smells (não bloqueante)

**Por que existe:** o relatório estrutural original não é reproduzível como ferramenta (o analisador não está no repositório). Três métricas permanecem sem origem: fan-in 57 de `solar_exception`, peso 127,6 do NOC e “effective code lines”.

**Ação:** obter o código/versão do analisador ou a data exata de geração. Sem isso, esses três números permanecem **não reproduzíveis**, e isso já está registrado.

**Impacto:** nenhum sobre as Etapas 2 e 3; apenas sobre a auditoria do relatório da Etapa 1.

---

## 8. O que NÃO precisa ser refeito

| Item                                   | Motivo                                                       |
| -------------------------------------- | ------------------------------------------------------------ |
| Recálculo de CC                        | Validado por API independente: 553/1.278/10/163              |
| Recálculo de LCOM1/LCOM4/TCC           | 39 classes, 0 divergências contra implementação independente |
| Recálculo de CBO das 5 maiores classes | Conjuntos idênticos                                          |
| Reprodução dos JSONs Radon             | 0 divergências em 208/269 arquivos                           |
| Recontagem de fan-in/fan-out           | 4 módulos conferidos; 0 imports não resolvidos               |
| Detecção de ciclos estáticos           | 0; matriz e SCC consistentes                                 |
| Contagem de módulos/classes            | 208/136 conferidos por AST                                   |
| Complexidade cognitiva                 | 300/794/18 reconferidos pela mesma ferramenta                |
| Tracing de runtime (P2)                | Executado em 3 cenários; resultados em `runtime_tracing/`    |

---

## 9. Critérios de encerramento formal

### Etapa 2

- [x] Fan-in, fan-out, instabilidade, grafo e ciclos medidos e verificados.
- [x] Coesão medida com aplicabilidade explícita; LCOM validado por implementação independente.
- [x] Distribuição por camada e subcamada publicada.
- [x] Alcançabilidade medida e caminhos alternativos investigados.
- [x] **Tracing de runtime executado (P2)** em 3 cenários; cobertura limitada documentada.
- [ ] **Decisão registrada** sobre o CBO: aceitar a aproximação **ou** executar P1.

Se as duas decisões forem “aceitar com limitação documentada”, a Etapa 2 está **encerrada com ressalvas** — sem trabalho adicional.

### Etapa 3

- [x] CC, tamanho de funções e de módulos medidos e verificados.
- [x] Complexidade cognitiva medida e reconferida.
- [x] Halstead e MI reproduzidos com fidelidade ao Radon.
- [x] Limitações de Halstead e MI quantificadas (52,62% de zeros; 52,9% de saturação).
- [x] Determinismo e reprodutibilidade comprovados.
- [ ] **Política do MI registrada** (P3) — 15 min.
- [ ] **Decisão registrada** sobre Halstead: declarar não aplicável **ou** executar P4.
- [ ] (Opcional) P5, se comparação com Sonar for exigida.

Se a política do MI for registrada e Halstead for formalmente declarado não aplicável, a Etapa 3 está **encerrada com ressalvas** — sem trabalho adicional.

---

## 10. Sequência mínima recomendada

1. **P3** (15 min) — registrar a política do MI.
2. Registrar em ata a decisão da Etapa 2 sobre o CBO (aproximação AST).
3. Registrar em ata a decisão da Etapa 3 (Halstead não aplicável).
4. Encerrar formalmente as duas etapas com as ressalvas de `CHECKLIST_FINAL.md`.

**Se o avaliador exigir o caminho rigoroso:** executar **P1 → P4 → P5**, nesta ordem. P2 (tracing) já foi executado; P1 fecha a Etapa 2; P4 e P5 fecham a Etapa 3 sem ressalvas de ferramenta.
