# Relatório técnico — Etapa 3: complexidade

**Projeto:** SOLAR
**Data:** 2026-10-23
**Ferramentas:** Radon 6.0.1; flake8 7.4.1 + flake8-cognitive-complexity 0.1.0
**Corpus de produção:** 208 módulos, 553 funções/métodos
**Código de produção alterado:** não

---

## 1. Pergunta e definições

A pergunta é: **onde está o custo de decisão e de leitura do código, e as
métricas usadas conseguem medi-lo?**

| Métrica                | Definição operacional            | Ferramenta    |
| ---------------------- | -------------------------------- | ------------- |
| CC                     | pontos de decisão + 1            | Radon `cc`    |
| Complexidade cognitiva | custo de leitura com aninhamento | plugin flake8 |
| Tamanho de função      | `endline − lineno + 1`           | Radon `cc`    |
| Halstead               | operadores/operandos e volume    | Radon `hal`   |
| LOC/SLOC/LLOC          | linhas físicas/de código/lógicas | Radon `raw`   |

**Não medido:** complexidade essencial, fan-in/fan-out de dados, profundidade de
herança e acoplamento aferente/eferente por classe.

---

## 2. Complexidade ciclomática

| Conjunto | N   | Soma  | Média | Mediana | P90 | Máx.   | Rank A      | Rank B    |
| -------- | --- | ----- | ----- | ------- | --- | ------ | ----------- | --------- |
| Produção | 553 | 1.278 | 2,31  | 2       | 5   | **10** | 523 (94,6%) | 30 (5,4%) |
| Testes   | 680 | 1.468 | 2,16  | 2       | 5   | 10     | 653         | 27        |

Nenhuma função atinge rank C (CC ≥ 11). A distribuição é fortemente concentrada
à esquerda: mediana 2 e apenas 30 funções com CC ≥ 6.

### 2.1 Maiores CC de produção

| Módulo                                                | Função                     | CC    | Linhas  |
| ----------------------------------------------------- | -------------------------- | ----- | ------- |
| `nucleus.rules.scanner.error_exposure_scanner`        | `_destination`             | 10    | 85      |
| `observatory.log.error_log`                           | `record`                   | 9     | 28      |
| `nucleus.rules.scanner.controller_return_scanner`     | `_scan_file`               | 8     | 58      |
| `nucleus.rules.scanner.error_exposure_scanner`        | `_detail`                  | 8     | 39      |
| `nucleus.rules.scanner.controller_auth_check_scanner` | `_checks` / `_abort_check` | 7 / 7 | 35 / 35 |

---

## 3. Complexidade cognitiva

**Método:** `flake8 --select=CCR --max-cognitive-complexity=0` sobre
`nucleus/`, `orbits/`, `observatory/solar/`, `observatory/log/` e `server.py`.

**Ressalva:** o plugin implementa uma versão inspirada na especificação do
Sonar; **não é o SonarQube oficial**. Os escores são comparáveis dentro do
projeto, não com relatórios externos.

| Estatística            | Valor        |
| ---------------------- | ------------ |
| Funções com escore ≥ 1 | 300          |
| Soma                   | 794          |
| Mediana                | 2            |
| Média                  | 2,65         |
| P90                    | 6            |
| Máximo                 | **18**       |
| Funções > 15           | **1** (0,3%) |

Maiores escores:

| Função                                     | Escore | CC  |
| ------------------------------------------ | ------ | --- |
| `ErrorExposureScanner._destination`        | 18     | 10  |
| `ControllerReturnScanner._scan_file`       | 14     | 8   |
| `TokenSecurityScanner._verifies_signature` | 13     | 7   |
| `UploadHandlingScanner._primitives`        | 10     | 7   |
| `Identity._persist`                        | 10     | 7   |

**Leitura:** a complexidade cognitiva acompanha a CC e confirma que o custo de
leitura está nos analisadores estáticos do Nucleus. Apenas `_destination` cruza
o limiar de 15; é também a função de maior CC e uma das mais longas.

---

## 4. Tamanho

| Estatística            | Valor         |
| ---------------------- | ------------- |
| N                      | 553           |
| Mín. / mediana / média | 2 / 13 / 16,6 |
| P90 / máximo           | 35 / **163**  |
| > 30 linhas            | 76 (13,7%)    |
| > 50 linhas            | 12 (2,2%)     |
| > 100 linhas           | 2 (0,4%)      |

Casos extremos:

- `Kernel.mount` — 163 linhas, **CC 2**: sequência de composição.
- `ArchitectureScanner._scan_file` — 108 linhas, CC 6.

**Interpretação:** o tamanho alto de `mount` é explicado pela função de
composição e pelos comentários; não há evidência de complexidade decisória.
Tamanho, isoladamente, não é defeito.

---

## 5. Halstead

| Estatística               | Valor              |
| ------------------------- | ------------------ |
| Módulos                   | 269                |
| Funções no JSON           | 1.219              |
| Funções com `N1 = N2 = 0` | 548 (44,95%)       |
| Produção (JSON)           | 290 de 552 (52,5%) |
| Volume total              | 20.003,46          |
| Volume de produção        | 6.130,70           |

**Limitação material:** o visitante Halstead do Radon não conta chamadas de
função (`Call`), acesso a atributos (`Attribute`) nem subscrito (`Subscript`).
Métodos que apenas orquestram chamadas recebem volume zero. O número é um
**limite inferior**, não uma medida de complexidade de expressão.

**Consequência:** Halstead não é usado para ranking nem para conclusão
arquitetural nesta auditoria.

---

## 6. Reprodutibilidade

| Relatório               | Arquivos comparados | Divergências                 |
| ----------------------- | ------------------- | ---------------------------- |
| `complexidade.json`     | 208                 | **0**                        |
| `halstead.json`         | 269                 | **0**                        |
| `tamanho.json`          | 269                 | **0**                        |
| `manutenibilidade.json` | 269                 | **0** (diferença máxima 0,0) |

Os JSONs foram regenerados em 2026-10-23 para o corpus atual, incluindo a
renomeação `observatory/records` → `observatory/log` e a suíte em
`observatory/tests/`. A reprodução integral está em `dados/validacao_radon.json`.

---

## 7. Limitações

1. **CC mede ramificação, não dificuldade conceitual.**
2. **Complexidade cognitiva não é Sonar oficial.**
3. **Halstead é inválido para mais da metade das funções.**
4. **Tamanho físico inclui docstrings e comentários.**
5. **Não há comparação histórica**; esta é uma fotografia.
6. **Não há estudo com mantenedores**; legibilidade não foi medida
   empiricamente.

---

## 8. Reprodução

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py
```

Para regenerar os JSONs brutos do Radon, use os caminhos de produção e teste
explicitamente, evitando incluir `observatory/audits`:

```powershell
py -m radon cc -j -a nucleus orbits observatory/__init__.py observatory/solar observatory/log observatory/tests server.py
```

---

## 9. Veredito da etapa

| Afirmação                                         | Veredito                              |
| ------------------------------------------------- | ------------------------------------- |
| A complexidade de controle é baixa na maior parte | **sustentada**                        |
| Há um outlier de legibilidade                     | **sustentada** (`_destination`)       |
| Halstead discrimina complexidade                  | **não sustentada**                    |
| A complexidade cognitiva é oficial                | **não sustentada** (plugin)           |
| O tamanho alto é defeito                          | **não sustentada** (depende do papel) |
