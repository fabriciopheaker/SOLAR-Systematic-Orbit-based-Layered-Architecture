# Resumo — Etapa 3: complexidade

## Números principais

| Indicador                                   | Valor                                                      |
| ------------------------------------------- | ---------------------------------------------------------- |
| Funções/métodos de produção                 | **553**                                                    |
| Soma de CC                                  | **1.278**                                                  |
| CC média / mediana                          | **2,31 / 2**                                               |
| CC P90 / máximo                             | **5 / 10**                                                 |
| Rank A / B                                  | **523 (94,6%) / 30 (5,4%)**                                |
| Rank C ou pior                              | **0**                                                      |
| Funções com complexidade cognitiva ≥ 1      | **300**                                                    |
| Soma cognitiva                              | **794**                                                    |
| Cognitiva mediana / P90 / máximo            | **2 / 6 / 18**                                             |
| Funções acima de 15 (limiar S3776)          | **1** (`_destination`, 18)                                 |
| Tamanho mediano / P90 / máximo              | **13 / 35 / 163** linhas                                   |
| Funções > 30 / > 50 / > 100 linhas          | **76 / 12 / 2**                                            |
| Halstead com `N1 = N2 = 0` (JSON, produção) | **290 de 552 (52,5%)**                                     |
| Volume Halstead de produção                 | **6.130,70**                                               |
| Reprodutibilidade Radon                     | **208/208 CC; 269/269 Halstead, raw e MI; 0 divergências** |

## O que os dados sustentam

1. **Não há hotspot generalizado de ramificação:** a CC mediana é 2 e nenhuma
   função atinge rank C.
2. **A complexidade cognitiva está no Nucleus:** 752 de 794 pontos (94,7%).
3. **Há um outlier de leitura:** `ErrorExposureScanner._destination` tem CC 10,
   cognitiva 18 e 85 linhas.
4. **O tamanho é dominado por funções curtas:** 76 funções passam de 30 linhas,
   mas apenas 2 passam de 100.
5. **Halstead não é utilizável como ranking nesta base:** mais da metade das
   funções tem volume zero por limitação do visitante do Radon.

## O que os dados **não** sustentam

| Afirmação                                    | Por que não                                           |
| -------------------------------------------- | ----------------------------------------------------- |
| “O código é complexo.”                       | A distribuição é fortemente à esquerda; 94,6% rank A. |
| “O código é simples.”                        | CC mede ramificação, não domínio; o outlier existe.   |
| “Halstead mede a complexidade de expressão.” | O visitante do Radon ignora chamadas e atributos.     |
| “A complexidade cognitiva é oficial.”        | O plugin é “sonar-like”, não SonarQube.               |
| “Funções longas são ruins.”                  | `Kernel.mount` tem 163 linhas e CC 2; é composição.   |

## Evidência principal

- `dados/funcoes_complexidade.csv`
- `dados/complexidade_cognitiva.csv`
- `dados/radon_halstead_modulos.csv`
- `dados/validacao_radon.json`
- `evidencias/AUDITORIA_ETAPA_3.md`

## Observação sobre MI

O MI do Radon é reproduzido com **0 divergências** (269/269), mas está saturado:
110 de 208 módulos de produção têm MI 100. Por isso a interpretação de
manutenibilidade foi movida para a **etapa 6**, onde o limite da métrica é
tratado como objeto de análise, não como conclusão.
