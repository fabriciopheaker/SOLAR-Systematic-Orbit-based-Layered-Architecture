# `observatory/audits/estrutural` — artefatos da análise estrutural SOLAR

Esta pasta contém **resultados e ferramentas** da análise quantitativa da arquitetura. O código de produção da aplicação (`nucleus/`, `orbits/`, `server.py`) não foi alterado; as ferramentas de auditoria vivem agora em `observatory/audits/`.

## Leitura recomendada

1. **`RELATORIO_CONSOLIDADO.md`** — relatório principal (metodologia, resultados, limitações, conclusões e pendências).
2. **`alertas_estruturais_revisados.csv`** — veredito para cada um dos 60 alertas do relatório original.
3. **`solar_acoplamento_modulos.csv`** — Ca, Ce, instabilidade e fan-in de testes por módulo.
4. **`solar_cbo_coesao_validacao.csv`** — coesão por classe, com aplicabilidade explícita de LCOM.
5. **`solar_ciclos_internos.json`** — ciclos estáticos e o ciclo dinâmico detectado.

## Auditoria final (Etapas 2 e 3)

A pasta **`auditoria_final/`** contém a avaliação formal das etapas de acoplamento/coesão e complexidade:

1. **`AUDITORIA_ETAPA_2.md`** — fan-in, fan-out, CBO, instabilidade, grafo, ciclos e coesão.
2. **`AUDITORIA_ETAPA_3.md`** — CC, complexidade cognitiva, tamanho, Halstead, MI e reprodutibilidade.
3. **`CHECKLIST_FINAL.md`** — status por item, evidência, justificativa e pendência.
4. **`PLANO_DE_ACAO.md`** — apenas as verificações restantes, priorizadas.
5. **`verificacoes_independentes.py`** / **`verificacoes.json`** — recálculo independente de CC, Halstead, MI, LCOM, CBO e acoplamento.

```powershell
py observatory/audits/estrutural/auditoria_final/verificacoes_independentes.py
```

## Scripts (reprodução)

```powershell
py -m pip install radon==6.0.1 flake8==7.4.1 flake8-cognitive-complexity==0.1.0
py observatory/audits/estrutural/solar_metrics.py       # todas as métricas próprias
py observatory/audits/estrutural/revisar_relatorio.py   # auditoria dos alertas originais
```

`solar_metrics.py` lê os JSONs de `reports/quality/` e grava/atualiza todos os CSV/JSON desta pasta.
`revisar_relatorio.py` depende das saídas do primeiro script.

## Mapa dos arquivos de saída

| Arquivo                                                                                        | Origem                         | Conteúdo                                                                           |
| ---------------------------------------------------------------------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------- |
| `modulos_metricas.csv`                                                                         | AST + Radon                    | consolidado por módulo (SLOC, CC, Halstead, MI, cognitiva, Ca/Ce, alcançabilidade) |
| `solar_acoplamento_modulos.csv`                                                                | grafo de imports               | Ca, Ce, I, fan-in de testes, CBO máx.                                              |
| `dependencias_internas.csv`                                                                    | grafo de imports               | 306 arestas internas com tipo e linhas                                             |
| `dependencias_externas.csv`                                                                    | grafo de imports               | imports de bibliotecas/stdlib (excluídos do acoplamento)                           |
| `solar_cbo_classes_estimado.csv`                                                               | AST (aproximação)              | CBO por classe (min/max e alvos)                                                   |
| `solar_cbo_coesao_validacao.csv` / `coesao_classes.csv`                                        | AST                            | atributos, métodos, LCOM1, LCOM\*, LCOM4, TCC, aplicabilidade                      |
| `solar_ciclos_internos.json` / `ciclos_scc.json`                                               | Tarjan                         | SCCs, ciclos e imports dinâmicos                                                   |
| `alcancabilidade.json`                                                                         | BFS                            | módulos não alcançáveis a partir de `server`/CLI                                   |
| `camadas_consolidado.csv`, `camadas_resumo.csv`, `subcamadas_resumo.csv`, `matriz_camadas.csv` | agregação                      | métricas por camada/subcamada e matriz de arestas                                  |
| `funcoes_complexidade.csv`                                                                     | Radon `cc`                     | 1.233 funções/métodos, com CC, rank, linhas e camada                               |
| `complexidade_cognitiva.csv`                                                                   | flake8-cognitive-complexity    | funções com escore ≥ 1                                                             |
| `radon_halstead_modulos.csv`                                                                   | Radon `hal`                    | volume/dificuldade/esforço e funções com Halstead zero                             |
| `validacao_radon.json`                                                                         | Radon API                      | prova de reprodução (0 divergências) e fórmula do MI                               |
| `resumo_metricas.json`                                                                         | agregação                      | todos os agregados em formato de máquina                                           |
| `alertas_estruturais_revisados.csv`                                                            | relatório original + recálculo | veredito por alerta                                                                |

## Convenções

- **Produção** = `.py` fora de `tests/`, `docs/`, `docker/`, `reports/`, `htmlcov/` e da pasta de dados `storage/`.
- **N/A** significa que a fórmula não tem domínio válido — nunca é convertido em zero.
- Métricas de acoplamento **não** incluem bibliotecas externas nem módulos de teste.
- Decimais com ponto nos CSV/JSON; vírgula no texto do relatório.
