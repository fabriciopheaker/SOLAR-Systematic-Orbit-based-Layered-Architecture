# Etapa 3 — Complexidade

**Pergunta:** onde está o custo de leitura e de decisão do código, e as métricas
de complexidade discriminam esse custo?

**Status:** concluída, com duas limitações materiais: Halstead do Radon não
conta chamadas/atributos; complexidade cognitiva usa plugin “sonar-like”, não o
SonarQube oficial.

## Artefatos

| Artefato                                                               | Conteúdo                                              |
| ---------------------------------------------------------------------- | ----------------------------------------------------- |
| [`RESUMO.md`](RESUMO.md)                                               | números principais e leitura curta                    |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md)                         | método, resultados, interpretação e limitações        |
| [`dados/funcoes_complexidade.csv`](dados/funcoes_complexidade.csv)     | CC, rank e tamanho por função de produção             |
| [`dados/complexidade_cognitiva.csv`](dados/complexidade_cognitiva.csv) | complexidade cognitiva por função                     |
| [`dados/radon_halstead_modulos.csv`](dados/radon_halstead_modulos.csv) | Halstead por módulo                                   |
| [`dados/validacao_radon.json`](dados/validacao_radon.json)             | reprodução integral do Radon                          |
| [`dados/radon/`](dados/radon/)                                         | JSONs brutos do Radon e relatório estrutural original |
| [`evidencias/AUDITORIA_ETAPA_3.md`](evidencias/AUDITORIA_ETAPA_3.md)   | auditoria independente da etapa                       |

## Reprodução

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py
```

O script lê os JSONs de `dados/radon/` e grava as saídas de complexidade em
`dados/`.

## Leitura de uma frase

A complexidade de controle é **baixa e concentrada**: 553 funções, CC mediana 2,
máximo 10, **94,6% rank A**. A complexidade cognitiva tem **uma única função
acima de 15** (`_destination`, 18). O problema não é complexidade generalizada;
é um outlier de leitura em um scanner e um conjunto de funções longas de
composição.
