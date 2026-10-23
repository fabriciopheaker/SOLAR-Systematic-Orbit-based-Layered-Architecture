# Benchmark comparativo — SOLAR × Clean Architecture × MVC × Hexagonal

**Status:** **estudo de viabilidade e plano metodológico concluídos; execução
empírica não realizada.**

Este diretório **não contém resultados comparativos**. Ele contém:

| Artefato                                         | Conteúdo                                                          |
| ------------------------------------------------ | ----------------------------------------------------------------- |
| [`RESUMO.md`](RESUMO.md)                         | conclusão de viabilidade em uma página                            |
| [`PLANO_DE_BENCHMARK.md`](PLANO_DE_BENCHMARK.md) | desenho experimental completo, métricas, ameaças e fases          |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md)   | análise de viabilidade, o que falta e o que não pode ser afirmado |
| [`dados/LEIA-ME.md`](dados/LEIA-ME.md)           | regra de integridade: nenhum dado inventado                       |

## Por que não há números comparativos

Comparar arquiteturas exige **implementações equivalentes do mesmo sistema**,
executadas no mesmo ambiente, com o mesmo conjunto de tarefas e medições
repetíveis. O repositório atual contém **uma** implementação (SOLAR); não contém
versões Clean Architecture, MVC e Hexagonal do mesmo sistema. Também não há:

- especificação funcional congelada para as quatro versões;
- harness de carga comum;
- ambiente controlado e repetível;
- conjunto de mantenedores para o estudo humano;
- requisitos de desempenho acordados.

Produzir “resultados” sem esses elementos seria comparar implementações
diferentes, com funcionalidades diferentes, em condições diferentes. Isso não é
benchmark; é anedota com tabela.

## O que este estudo entrega agora

1. Uma pergunta de pesquisa falsificável.
2. A definição operacional de cada arquitetura.
3. O sistema de referência e os cenários de mudança.
4. As métricas e os critérios de aceite.
5. O desenho estatístico e as ameaças à validade.
6. O pacote de reprodutibilidade necessário.
7. Um cronograma e uma estimativa de esforço.

## O que este estudo não entrega

- ranking de arquiteturas;
- “SOLAR é X% melhor”;
- latência comparativa;
- custo de manutenção comparativo;
- conclusão causal sobre qual arquitetura é superior.
