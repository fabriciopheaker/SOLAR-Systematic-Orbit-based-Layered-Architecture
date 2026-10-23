# Resumo — Etapa 2: acoplamento, coesão e dependências

## Números principais

| Indicador                                    | Valor                                                                        |
| -------------------------------------------- | ---------------------------------------------------------------------------- |
| Módulos de produção                          | **208**                                                                      |
| Módulos de teste                             | **61**                                                                       |
| Arestas internas                             | **306**                                                                      |
| Arestas intra-camada                         | **276 (90,2%)**                                                              |
| Arestas entre camadas                        | **30 (9,8%)**                                                                |
| Densidade do grafo                           | **0,71%**                                                                    |
| Ciclos estáticos                             | **0**                                                                        |
| Ciclos totais (AST + imports dinâmicos)      | **1** (`Database ↔ user_model`)                                              |
| Ce mediano / máximo                          | **3 / 49** (`project_validator`)                                             |
| Ca mediano / máximo                          | **1 / 38** (`solar_exception`)                                               |
| Classes                                      | **136**                                                                      |
| CBO mediano / máximo                         | **1 / 15** (`Kernel`)                                                        |
| LCOM aplicável                               | **39 (28,7%)**                                                               |
| LCOM não aplicável                           | **97 (71,3%)**                                                               |
| LCOM1 mediano (n=39)                         | **3**                                                                        |
| LCOM4 máximo                                 | **3**                                                                        |
| TCC mediano (n=39)                           | **0,30**                                                                     |
| Módulos não alcançáveis (estático)           | **15**, com **631 SLOC**                                                     |
| Ausentes confirmados em runtime (3 cenários) | **14**, com **625 SLOC (9,98%)**; `observatory.log` refutado como pacote-pai |

## O que os dados sustentam

1. **Acoplamento interno baixo e esparso:** 306 arestas para 208 módulos;
   densidade de 0,71%.
2. **Concentração em pontos arquiteturais:** `project_validator` (Ce 49) é o
   registro de regras; `Kernel` (CBO 15) é o composition root;
   `solar_exception` (Ca 38) é a base de exceções.
3. **Ciclo é temporal, não caótico:** o ciclo `Database ↔ user_model` existe
   porque o Model usa `Database.orm` no momento do import; o `Database` importa
   Models dinamicamente. Há dependência de ordem, não falha observada.
4. **Coesão é limitada pela natureza das classes:** 97 classes não têm estado
   de instância aplicável; LCOM1 alto em scanners reflete classes com um único
   atributo e muitos métodos, não necessariamente baixa coesão de domínio.

## O que os dados **não** sustentam

| Afirmação                         | Por que não                                                            |
| --------------------------------- | ---------------------------------------------------------------------- |
| “O acoplamento é um problema.”    | Os maiores valores têm papel arquitetural declarado.                   |
| “O ciclo causa falhas.”           | Não houve falha observada; há dependência de ordem.                    |
| “A coesão é ruim.”                | LCOM não se aplica a 97 classes; LCOM1 cresce com o número de métodos. |
| “Os 15 módulos são código morto.” | Ausência no grafo estático não prova desuso.                           |
| “O CBO é absoluto.”               | É uma aproximação por AST, sem resolução de tipos.                     |

## Evidência principal

- `dados/resumo_metricas.json`
- `dados/solar_acoplamento_modulos.csv`
- `dados/coesao_classes.csv`
- `dados/classes_cbo.csv`
- `dados/solar_ciclos_internos.json`
- `dados/alcancabilidade.json`
- `evidencias/AUDITORIA_ETAPA_2.md`
- `evidencias/runtime_tracing/RELATORIO_RUNTIME_TRACING.md`

## Auditoria dos alertas originais

Dos **60 alertas** do relatório estrutural original:

| Veredito                          | Quantidade |
| --------------------------------- | ---------- |
| Confirmado                        | 7          |
| Falso positivo                    | 7          |
| Parcial                           | 43         |
| Não reproduzível                  | 1          |
| Confirmado fora do escopo (teste) | 2          |

**Leitura:** a maior parte dos alertas é parcial porque a ferramenta original
mistura populações (produção + testes + dependências externas) e usa limiares
não declarados. O dado reproduzível é o recalculado neste diretório.
