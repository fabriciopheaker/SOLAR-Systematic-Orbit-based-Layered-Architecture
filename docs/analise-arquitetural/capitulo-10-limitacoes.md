# Capítulo 10 — Limitações

> **Pergunta deste capítulo:** o que este conjunto de resultados **não** consegue provar?

---

## 10.1 Limitação, pendência e erro

| Conceito        | Definição                                        | Exemplo no SOLAR               |
| --------------- | ------------------------------------------------ | ------------------------------ |
| **Limitação**   | fronteira inerente ao método                     | AST não resolve tipos          |
| **Pendência**   | verificação possível, ainda não executada        | CBO tipado; Sonar oficial      |
| **Erro**        | resultado incorreto por defeito de implementação | um parser que perdesse imports |
| **Aproximação** | resultado útil, mas não exato                    | CBO por AST                    |
| **Lacuna**      | ausência de dado necessário para concluir        | cobertura de testes            |

Uma limitação não invalida o resultado; delimita a conclusão. Uma pendência não é limitação permanente; é trabalho futuro. Um erro precisa ser corrigido.

---

## 10.2 Limitações de ferramenta

| Limitação                                         | Ferramenta                  | Efeito no SOLAR                                           | Mitigação                                        |
| ------------------------------------------------- | --------------------------- | --------------------------------------------------------- | ------------------------------------------------ |
| Visitor de Halstead não visita `Call`/`Subscript` | Radon                       | 291 de 553 funções de produção com `n1 = n2 = 0` (52,62%) | declarar; não usar Halstead como medida completa |
| MI satura com volume zero                         | Radon                       | 110 de 208 módulos com MI 100                             | usar CC/cognitiva/tamanho em conjunto            |
| MI sensível a comentários                         | Radon                       | `http_input`: 32,26 → 79,88 sem docstrings                | analisar composição antes de concluir            |
| Cognitive plugin não é oficial                    | flake8-cognitive-complexity | valores “sonar-like”, não Sonar                           | não comparar numericamente com Sonar             |
| Rank A–F é convenção                              | Radon                       | CC 10 é rank B, não “defeito”                             | citar origem do limite                           |
| Halstead por função perde homônimos no JSON       | Radon/serialização          | 14 homônimos (1 na produção)                              | usar CSV/API quando precisar do detalhe          |

---

## 10.3 Limitações de implementação

| Limitação                               | Onde               | Efeito                                                   | Mitigação                                   |
| --------------------------------------- | ------------------ | -------------------------------------------------------- | ------------------------------------------- |
| CBO por AST não resolve tipos           | `solar_metrics.py` | valores aproximados; não comparáveis a ferramenta tipada | declarar aproximação; CBO tipado pendente   |
| LCOM1 cresce com número de métodos      | fórmula            | `ErrorExposureScanner` 89 com 14 métodos                 | usar LCOM4/TCC em conjunto                  |
| LCOM não vê estado de classe            | fórmula            | `Database`/`Storage` N/A                                 | registrar N/A; não tratar como baixa coesão |
| Ramos/aninhamento sem definição única   | recálculo          | aninhamento reproduzido em 2 de 35                       | não usar o detalhe como prova               |
| Grafo estático não vê imports dinâmicos | AST                | ciclo `Database ↔ user_model` só apareceu no runtime     | tracing + modelagem de alvos dinâmicos      |
| BFS depende dos pontos de entrada       | alcançabilidade    | 134/208; se `token` for entry point, muda                | declarar entry points; testar cenários      |

---

## 10.4 Limitações de configuração

| Configuração                                | Efeito                            | Exemplo                              |
| ------------------------------------------- | --------------------------------- | ------------------------------------ |
| `tests/` incluído nos relatórios Radon      | médias e volumes misturados       | CC total inclui 680 funções de teste |
| Exclusão de testes nas métricas de produção | conjunto menor e mais preciso     | 553 funções, 6.265 SLOC              |
| `count_multi=True` no MI                    | docstrings contam como comentário | `http_input` 393,33% de comentários  |
| Versões de Radon/flake8                     | resultados podem variar           | 6.0.1 / 7.4.1 registrados            |
| Caminhos absolutos e timestamps             | saídas não determinísticas        | normalização para hash               |

**Lição:** configurar não é “detalhe”. A mesma métrica com escopos diferentes produz números diferentes e conclusões diferentes.

---

## 10.5 Limitações de cobertura

| Cobertura                  | O que cobre             | O que não cobre                  |
| -------------------------- | ----------------------- | -------------------------------- |
| Análise estática           | todo o código parseável | execução, tipos, reflexão        |
| Runtime A (verificador)    | caminho do validador    | rotas, middlewares               |
| Runtime B (bootstrap)      | composição do Kernel    | requisições HTTP                 |
| Runtime C (modelo isolado) | dependência do modelo   | fluxo normal                     |
| 3 cenários                 | 175 módulos observados  | jobs, CLI, caminhos de erro      |
| Testes existentes          | comportamento testado   | cobertura e eficácia não medidas |

**Consequência:** os 14 módulos ausentes podem ser usados em fluxos não exercitados. A ausência é um achado de cobertura, não uma prova de desuso.

---

## 10.6 Falsos positivos e falsos negativos

| Caso                                              | Tipo                          | Por que acontece                                                    | Lição                                       |
| ------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------- | ------------------------------------------- |
| LCOM 15 em `Database`                             | falso positivo                | LCOM1 sobre classe sem atributos gera `C(6,2)`                      | aplicar pré-condição                        |
| LCOM 15 em `Storage`                              | falso positivo                | idem                                                                | idem                                        |
| LCOM 21 em `DatabaseDriver`                       | falso positivo                | idem                                                                | idem                                        |
| Fan-in 57 em `solar_exception`                    | parcial                       | valor mistura produção (38) e parte dos testes (25); total atual 63 | separar produção de teste antes de comparar |
| Fan-in com `pathlib`/`pytest`/`dataclasses`/`ast` | falso positivo                | contagem de externos como internos                                  | separar interno/externo                     |
| “0 abstratas” no NOC                              | erro de relatório             | 9 classes herdam de ABC/Protocol                                    | recalcular                                  |
| Ciclo não detectado no estático                   | falso negativo                | import dinâmico                                                     | tracing                                     |
| Módulo usado só em teste                          | falso positivo de “não usado” | análise de produção ignora testes                                   | declarar escopo                             |

**Nenhuma ferramenta é isenta.** A questão não é “há FP/FN?”, mas “eles estão declarados e tratados?”.

---

## 10.7 Ausência de limites universais

Não existe um número universal para:

- CC “aceitável”;
- CBO “máximo”;
- LCOM “máximo”;
- MI “mínimo”;
- Ce “máximo”.

Os valores usados como referência são **convenções**:

- ranks do Radon;
- limiar 15 da regra S3776 do Sonar;
- heurísticas de literatura.

Usá-los sem citar a origem transforma convenção em dogma. Nesta documentação, todo limite é acompanhado de “segundo a ferramenta X” ou “convenção de Y”.

---

## 10.8 Reprodutibilidade ≠ interpretação

| Afirmação                              | Tipo           | Status      |
| -------------------------------------- | -------------- | ----------- |
| “553 funções de produção”              | reproduzível   | validado    |
| “CC total 1.278”                       | reproduzível   | validado    |
| “LCOM1 = 89 em `ErrorExposureScanner`” | reproduzível   | validado    |
| “O código é fácil de manter”           | interpretativo | não provado |
| “Os 14 módulos são inúteis”            | interpretativo | não provado |
| “O ciclo causa problema”               | interpretativo | não provado |

**Reprodutibilidade** garante que o número pode ser recalculado. **Interpretação** exige contexto, leitura e, às vezes, dados que não foram coletados.

---

## 10.9 Métrica ≠ qualidade percebida

| Métrica              | O que mede                 | O que não mede                        |
| -------------------- | -------------------------- | ------------------------------------- |
| CC                   | caminhos                   | clareza dos nomes, coesão do contrato |
| CBO                  | classes referenciadas      | qualidade da dependência              |
| LCOM                 | compartilhamento de estado | coesão conceitual                     |
| MI                   | fórmula composta           | experiência de manutenção             |
| Alcançabilidade      | caminhos de import         | valor de uma API pública              |
| Cobertura de runtime | cenários executados        | qualidade dos testes                  |

A qualidade percebida por quem mantém envolve história, domínio, documentação, testes, revisão e cultura. Nenhuma métrica isolada captura isso.

---

## 10.10 Limitações específicas do SOLAR

| Caso                            | Limitação                                        | Consequência                                   |
| ------------------------------- | ------------------------------------------------ | ---------------------------------------------- |
| `Kernel` CBO 15                 | composition root                                 | alto por papel; não é defeito                  |
| `project_validator` Ce 49       | registro de regras                               | alto por papel; não é defeito                  |
| `ErrorExposureScanner` LCOM1 89 | 14 métodos, 1 atributo                           | alto por construção; LCOM4 1                   |
| `Database`/`Storage` LCOM       | sem estado de instância                          | N/A; não é baixa coesão                        |
| `http_input` MI 32,26           | comentários/docstrings                           | MI não representa manutenibilidade             |
| `_destination` cognitiva 18     | outlier                                          | risco de leitura/teste, não defeito            |
| 14 módulos ausentes             | 3 cenários                                       | funcionalidade não conectada, não código morto |
| ciclo `Database ↔ user_model`   | ordem de inicialização                           | risco de erro, não falha observada             |
| ROF-003                         | regra sem scanner no `check`; com teste unitário | conformidade parcial nesse ponto               |

---

## 10.11 O que permanece pendente

| Pendência                      | Por que importa                   | O que seria necessário                       |
| ------------------------------ | --------------------------------- | -------------------------------------------- |
| CBO com resolução de tipos     | comparar com ferramentas tipadas  | `mypy`/`pyright`/`jedi` ou análise semântica |
| Complexidade cognitiva oficial | comparar com Sonar                | SonarQube/SonarCloud                         |
| Halstead por função completo   | evitar 52,62% de zeros            | visitor com `Call`/`Subscript`               |
| MI com poder de discriminação  | ordenar módulos                   | volume calculável + política de comentários  |
| Evolução histórica             | medir tendência                   | série de commits/versões                     |
| Cobertura de testes            | saber o que é testado             | coverage + testes                            |
| Tracing de rotas               | cobrir HTTP                       | cenário com requisições                      |
| Eficácia das regras            | saber se as regras pegam defeitos | corpus com defeitos injetados                |

**Nenhuma pendência foi apresentada como concluída.** Onde o dado não existe, a documentação diz que não existe.

---

## 10.12 O que foi preservado

- Nenhum código de produção foi alterado.
- Nenhum relatório original foi substituído.
- As ressalvas dos relatórios de auditoria foram mantidas.
- As aproximações foram declaradas como aproximações.
- Os resultados desfavoráveis não foram escondidos.
- As pendências foram listadas.

---

## 10.13 Resumo do capítulo

- Limitação, pendência, erro, aproximação e lacuna são coisas diferentes.
- Ferramentas têm pontos cegos; implementações têm pré-condições; configurações mudam números.
- A cobertura de runtime é parcial; ausência não é prova.
- Falsos positivos e negativos existem e foram documentados.
- Não há limites universais; há convenções e contexto.
- Reprodutibilidade não é interpretação; métrica não é qualidade percebida.

**Próximo:** [Capítulo 11](capitulo-11-roteiro-pratico.md) — como repetir a análise e interpretar dois casos concretos.
