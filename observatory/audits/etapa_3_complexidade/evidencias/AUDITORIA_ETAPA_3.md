# AUDITORIA — ETAPA 3 (Complexidade e Manutenibilidade)

> **Nota de reorganização (2026-10-23):** este parecer é histórico. Caminhos
> `observatory/audits/estrutural/` e `reports/quality/` foram movidos para
> `observatory/audits/etapa_2_acoplamento_coesao/` e
> `observatory/audits/etapa_3_complexidade/dados/radon/`. Os números atuais
> estão no `RELATORIO_TECNICO.md` da etapa 3.

**Arquitetura avaliada:** SOLAR (`nucleus/`, `orbits/`, `observatory/`, `server.py`)
**Data:** 22/10/2026
**Base auditada:** `observatory/audits/estrutural/` (commit `1b39b8e`, árvore de trabalho limpa)
**Verificação independente:** `observatory/audits/estrutural/auditoria_final/verificacoes_independentes.py` → `verificacoes.json`
**Nenhum código-fonte da SOLAR foi alterado.**

---

## 1. Método

1. Leitura integral do relatório consolidado e dos scripts que geraram os números.
2. Recálculo independente com a **API do Radon** (não com o JSON do CLI) de CC, Halstead por função e MI.
3. Comparação com os artefatos publicados (`funcoes_complexidade.csv`, `radon_halstead_modulos.csv`, `modulos_metricas.csv`).
4. Reexecução do `flake8-cognitive-complexity` e comparação com `complexidade_cognitiva.csv`.
5. Teste de determinismo: os scripts foram executados duas vezes e os hashes dos artefatos comparados.
6. Correção das divergências encontradas **no relatório/script de análise** (nunca no código da SOLAR).

**Ambiente:** Python 3.14.7 · Radon 6.0.1 · flake8 7.4.1 · flake8-cognitive-complexity 0.1.0.

---

## 2. Complexidade ciclomática (CC)

### 2.1 Definição e escopo

Radon define CC como `pontos de decisão + 1`. Blocos de classe **não** entram na soma (o Radon os reporta separadamente; somá-los duplicaria os métodos). Escopo: 553 funções e métodos de produção (exclui `tests/`).

### 2.2 Resultados

| Conjunto | N   | Soma  | Média | Mediana | P90 | Máx.   | Rank A      | Rank B    |
| -------- | --- | ----- | ----- | ------- | --- | ------ | ----------- | --------- |
| Produção | 553 | 1.278 | 2,31  | 2       | 5   | **10** | 523 (94,6%) | 30 (5,4%) |
| Testes   | 680 | 1.468 | 2,16  | 2       | 5   | 10     | 653         | 27        |

**Verificação independente (V2) — API do Radon, contagem própria:**

| Métrica                    | Independente | Publicado | Divergência |
| -------------------------- | ------------ | --------- | ----------- |
| Funções/métodos (produção) | 553          | 553       | 0           |
| Soma de CC                 | 1.278        | 1.278     | 0           |
| CC máxima                  | 10           | 10        | 0           |
| Maior função (linhas)      | 163          | 163       | 0           |

**Status: VALIDADO.** O cálculo é reprodutível e a contagem não está inflada por duplicação de métodos.

### 2.3 Casos extremos

| Módulo                                            | Função         | CC  | Linhas |
| ------------------------------------------------- | -------------- | --- | ------ |
| `nucleus.rules.scanner.error_exposure_scanner`    | `_destination` | 10  | 85     |
| `observatory.records.error_log`                   | `record`       | 9   | 28     |
| `nucleus.rules.scanner.controller_return_scanner` | `_scan_file`   | 8   | 58     |
| `nucleus.rules.scanner.error_exposure_scanner`    | `_detail`      | 8   | 39     |

**Limites usados:** os ranks A–F são os **padrões do Radon** (A: 1–5; B: 6–10; C: 11–20; D: 21–30; E: 31–40; F: ≥41), não limites universais. Mesmo adotando um corte conservador de 10, apenas **1 função** atinge o limite e nenhuma o ultrapassa.

**Interpretação:** não há hotspot de ramificação. A maior CC do projeto (10) é a de uma função de análise sintática com 85 linhas — plausível para o domínio. Não há evidência de que a arquitetura produza funções complexas.

---

## 3. Complexidade cognitiva

### 3.1 Ferramenta e escopo

`flake8 --select=CCR --max-cognitive-complexity=0` com `flake8-cognitive-complexity` 0.1.0, sobre `nucleus/`, `orbits/`, `observatory/` e `server.py`. Com limiar 0, toda função com escore ≥ 1 é emitida; ausência = 0.

**Ressalva de ferramenta:** o plugin implementa uma versão inspirada na especificação de Sonar; **não é o SonarQube oficial**. Os escores não são comparáveis com relatórios de outras ferramentas.

### 3.2 Resultados

| Estatística            | Valor               |
| ---------------------- | ------------------- |
| Funções com escore ≥ 1 | 300 (54,2% das 553) |
| Soma                   | 794                 |
| Mediana                | 2                   |
| Média                  | 2,65                |
| P90                    | 6                   |
| Máximo                 | **18**              |
| Funções > 15           | **1** (0,3%)        |

**Verificação independente (V8):** 300 funções, soma 794, máximo 18, mesmos 5 maiores escores → **0 divergências**.

**Maiores escores:**

| Função                                     | Escore | CC  | Linhas |
| ------------------------------------------ | ------ | --- | ------ |
| `ErrorExposureScanner._destination`        | 18     | 10  | 85     |
| `ControllerReturnScanner._scan_file`       | 14     | 8   | 58     |
| `TokenSecurityScanner._verifies_signature` | 13     | —   | —      |
| `UploadHandlingScanner._primitives`        | 10     | —   | —      |
| `Identity._persist`                        | 10     | —   | —      |

**Distribuição por camada:** Nucleus 752 (94,7%), Observatory 30, Bootstrap 5, Orbits/Planets 5, Orbits/Database 2, Orbits 0.

**Sobre o limiar de 15:** é o valor padrão da regra **S3776 do SonarQube**, usado aqui apenas como referência externa. Não é limite universal. A conclusão relevante não depende dele: **apenas 1 função** está muito acima das demais (18 vs. P90 = 6), e ela também concentra a maior CC.

**Interpretação:** `_destination` é o único candidato claro a revisão de legibilidade (não de correção). As demais funções estão na faixa 1–14, compatível com código de análise sintática.

---

## 4. Tamanho de funções e módulos

### 4.1 Funções

| Métrica                | Valor         |
| ---------------------- | ------------- |
| N                      | 553           |
| Mín. / Mediana / Média | 2 / 13 / 16,6 |
| P90 / Máx.             | 35 / **163**  |
| > 30 linhas            | 76 (13,7%)    |
| > 50 linhas            | 12 (2,2%)     |
| > 100 linhas           | 2 (0,4%)      |

**Definição:** `endline − lineno + 1` (linhas físicas, incluindo docstring e comentários internos). Não é “linhas lógicas”.

**Casos extremos:**

- `Kernel.mount` — 163 linhas, **CC = 2**. É uma sequência de montagem (ambiente, identidade, banco, storage, broadcast, middlewares, rotas). O risco é de **extensão/manutenção**, não de ramificação.
- `ArchitectureScanner._scan_file` — 108 linhas, CC = 6.

**Interpretação:** o tamanho alto de `mount` é explicado pela função de composição e comentários; não há evidência de complexidade decisória. Não é um defeito por si.

### 4.2 Módulos (SLOC)

| Módulo                                          | SLOC | LLOC | Funções | Soma CC |
| ----------------------------------------------- | ---- | ---- | ------- | ------- |
| `nucleus.rules.scanner.error_exposure_scanner`  | 273  | 164  | 17      | 79      |
| `nucleus.rules.project_validator`               | 269  | 107  | 6       | 16      |
| `nucleus.rules.scanner.mass_assignment_scanner` | 159  | 109  | 11      | 44      |
| `observatory.records.error_log`                 | 159  | 78   | 12      | 28      |
| `nucleus.rules.scanner.secret_scanner`          | 144  | 70   | 8       | 26      |

**Verificação:** `tamanho.json` (Radon `raw`) reproduzido em **269/269 arquivos** (loc, lloc, sloc, comments). Os valores são os do Radon; “SLOC” conta linhas de código (sem branco/comentário).

---

## 5. Halstead

### 5.1 Definições

η1/N1 = operadores distintos/total; η2/N2 = operandos distintos/total; `V = N·log₂(η)`; `D = (η1/2)·(N2/η2)`; `E = D·V`; `B = V/3000`.

### 5.2 Reprodutibilidade

| Artefato                                  | Arquivos | Divergências |
| ----------------------------------------- | -------- | ------------ |
| `halstead.json` (volume total por módulo) | 269      | **0**        |

### 5.3 Limitação estrutural (verificada no código do Radon)

O visitante do Radon (`radon.visitors.HalsteadVisitor`) implementa apenas:

```
visit_BinOp, visit_UnaryOp, visit_BoolOp, visit_Compare,
visit_AugAssign, visit_FunctionDef, visit_AsyncFunctionDef
```

**Não há `visit_Call` nem `visit_Subscript`.** Chamadas de função e indexação não são contadas como operadores; `Attribute` aparece apenas como tipo de operando, não como operador. Consequência: métodos que apenas orquestram chamadas recebem `N1 = N2 = 0`.

### 5.4 Contagens corretas (correção desta auditoria)

| Base                                  | Funções   | N1 = N2 = 0 | Proporção  |
| ------------------------------------- | --------- | ----------- | ---------- |
| API do Radon (lista) — corpus         | **1.233** | **561**     | **45,50%** |
| `halstead.json` (dicionário) — corpus | 1.219     | 548         | 44,95%     |
| API — produção                        | **553**   | **291**     | **52,62%** |

**Duas diferenças explicadas:**

1. **Colisões de nomes no JSON:** o CLI grava `functions` como dicionário por nome; métodos homônimos em classes diferentes sobrescrevem um ao outro. Perdem-se **14 funções** (1 na produção: `nucleus/rules/report.py`, onde `status` existe em duas classes; 13 em testes).
2. **Definições ausentes na lista do Halstead:** o AST contém **1.242** definições de função (das quais **15** têm outra função como pai); a lista do Halstead tem **1.233**. O delta observado é **9**; ele não deve ser atribuído apenas a funções aninhadas — a decomposição exata desse delta não foi verificada.

O volume total por módulo **não** é afetado por colisões (é agregado no visitante raiz); apenas a análise **por função** é afetada.

### 5.5 Volume

| Base                   | Volume               |
| ---------------------- | -------------------- |
| Corpus (269 módulos)   | 19.918,75            |
| Produção (208 módulos) | **6.094,74** (30,6%) |
| Testes (61 módulos)    | 13.824,01 (69,4%)    |

**Maiores volumes de produção:** `error_exposure_scanner` 555,89 (4 de 17 funções com zero), `token_security_scanner` 276,74, `mass_assignment_scanner` 230,82, `error_log` 201,91 (**8 de 12** com zero), `url_guard` 201,18.

**Interpretação:** Halstead é utilizável como **limite inferior** de volume por módulo e **não é utilizável** como medida de complexidade por função nesta base. Os números são reproduzíveis, mas a métrica não mede o que se pretende.

**Status:** VALIDADO COM RESSALVAS (reprodução) / **NÃO APLICÁVEL** como evidência de complexidade por função.

---

## 6. Índice de manutenibilidade (MI)

### 6.1 Fórmula (confirmada no código do Radon)

```
MI = max(0, min(100, (171 − 5,2·ln V − 0,23·CC − 16,2·ln LLOC
                        + 50·sen(√(2,46·rad(%comentários)))) · 100/171))
```

com `V` = volume Halstead total, `CC` = `ComplexityVisitor.total_complexity`, `LLOC` = `raw.lloc`, `%comentários = (comments + multi)/sloc·100`. Se `V ≤ 0` ou `LLOC ≤ 0` → **100,0**.

### 6.2 Reprodutibilidade

**269/269 arquivos** recalculados com `radon.metrics.mi_visit` → **0 divergências** (diferença máxima 0,0).

### 6.3 Resultados

| Conjunto | N   | Mín.  | Mediana   | Média | Rank A     |
| -------- | --- | ----- | --------- | ----- | ---------- |
| Corpus   | 269 | 32,26 | 87,82     | 84,53 | 269 (100%) |
| Produção | 208 | 32,26 | **100,0** | 88,14 | 208 (100%) |

### 6.4 Por que a métrica não discrimina

| Fato                             | Valor           |
| -------------------------------- | --------------- |
| Módulos de produção com MI = 100 | **110 (52,9%)** |
| Desses, com `V = 0`              | **110**         |
| Desses, com SLOC > 0             | 50              |

Ou seja: mais da metade dos módulos recebe 100 **não por serem simples**, mas porque o Halstead não encontra operadores (`V = 0`). Exemplos com SLOC > 0: `nucleus/exceptions/*` (3–4 SLOC), `nucleus/contracts/validator.py` (5 SLOC), `nucleus/database/drivers/interface/database_driver.py` (23 SLOC, só métodos abstratos com `raise NotImplementedError`).

### 6.5 Distorção pelo termo de comentários

O mínimo (32,26) é `nucleus/contracts/http_input.py`: **15 SLOC**, LLOC 23, V 86,04, CC 3. O percentual de comentários calculado pelo Radon é **393,33%** (docstring multilinha sobre 15 SLOC), tornando o termo senoidal negativo.

**Sensibilidade (reproduzível):** com `count_multi=False` (docstrings não contam como comentário):

- 26 de 208 módulos variam mais de 10 pontos;
- delta médio **+2,87**;
- maior variação **+47,62** (`http_input`: 32,26 → 79,88);
- mínimo sobe para 50,35.

**Interpretação:** o MI publicado é aritmeticamente correto e reproduzível, mas **não é um indicador útil nesta base**: 100% rank A, metade saturada em 100 e o mínimo é um artefato do termo de comentários.

**Status:** VALIDADO (reprodução) / **NÃO APLICÁVEL** como discriminador de manutenibilidade.

---

## 7. Reprodutibilidade e limitações metodológicas

### 7.1 Prova de reprodução

| Relatório                    | Arquivos    | Divergências       |
| ---------------------------- | ----------- | ------------------ |
| `complexidade.json`          | 208         | **0**              |
| `halstead.json`              | 269         | **0**              |
| `tamanho.json`               | 269         | **0**              |
| `manutenibilidade.json`      | 269         | **0**              |
| `complexidade_cognitiva.csv` | 300 funções | **0** (300/794/18) |

### 7.2 Determinismo

Os scripts `solar_metrics.py` e `revisar_relatorio.py` foram executados duas vezes. Após a correção de ordenação de empates, os hashes de todos os CSV/JSON são **idênticos**. Antes da correção, apenas a ordem de itens empatados em `top_instability` variava (nenhum valor numérico mudava).

### 7.3 O que **não** foi medido / não é medível com o corpus atual

- complexidade essencial e fluxo de dados;
- Halstead com visitante completo (chamadas, atributos, subscritos);
- MI com política alternativa oficial (apenas sensibilidade calculada);
- complexidade cognitiva no SonarQube oficial;
- evolução histórica (uma única fotografia);
- métricas de execução (fora do escopo; Etapa 4).

### 7.4 Correções aplicadas nesta auditoria

| Item                         | Antes                         | Depois                                                          | Motivo                                 |
| ---------------------------- | ----------------------------- | --------------------------------------------------------------- | -------------------------------------- |
| Contagem de funções Halstead | 1.219                         | 1.233 (API) / 1.219 (JSON)                                      | colisões de nomes no dicionário do CLI |
| Proporção de zeros           | 44,95%                        | 45,50% (API) / 44,95% (JSON) / **52,62% (produção)**            | separação produção/teste e colisões    |
| Arquivos sem CC              | “61 `__init__.py` vazios”     | 59 inits sem código + 1 init com reexportações + 1 módulo vazio | verificação arquivo a arquivo          |
| Ordenação de rankings        | não determinística em empates | determinística                                                  | reprodutibilidade byte a byte          |

---

## 8. Conclusão da Etapa 3

**Pode ser formalmente concluída?** **Sim, com ressalvas registradas.**

Justificativa:

- **CC, tamanho e complexidade cognitiva** estão medidos, reproduzidos e verificados de forma independente (V2, V8) — **validados**.
- **Halstead e MI** estão medidos e reproduzidos com fidelidade ao Radon (0 divergências), mas **não são interpretáveis como evidência de qualidade** nesta base (45,50% de funções com Halstead zero; 52,9% dos módulos com MI saturado em 100). O achado “não usar essas métricas como prova” é, ele próprio, sustentado pelos dados.
- Nenhum item obrigatório ficou sem medição. As pendências restantes são de **ferramenta alternativa** (Sonar oficial, visitante Halstead completo), não de dados ausentes.

**Pendências que impediriam o encerramento:** apenas `P2` (Halstead completo) e `P3` (Sonar oficial), e somente se o protocolo exigir essas métricas como evidência — o que os dados atuais desaconselham.
