# Resumo — Benchmark comparativo

## Conclusão

**Não é possível entregar um benchmark empírico confiável com os artefatos
atuais.** É possível entregar um plano experimental detalhado e reproduzível, e
é isso que este diretório faz.

| Requisito para benchmark                     | Existe hoje?                                              |
| -------------------------------------------- | --------------------------------------------------------- |
| Implementação SOLAR                          | **sim**                                                   |
| Implementação Clean Architecture equivalente | **não**                                                   |
| Implementação MVC equivalente                | **não**                                                   |
| Implementação Hexagonal equivalente          | **não**                                                   |
| Especificação funcional congelada            | **não**                                                   |
| Harness de carga comum                       | **não** (existe apenas o da etapa 4, específico da SOLAR) |
| Ambiente controlado/repetível                | **parcial** (uma máquina, uma execução)                   |
| Requisitos de desempenho                     | **não**                                                   |
| Pool de mantenedores                         | **não**                                                   |
| Série histórica                              | **não**                                                   |

## O que seria comparado

O mesmo sistema de referência — cadastro de usuários, autenticação, consulta,
upload e health check — implementado quatro vezes com as mesmas
funcionalidades, o mesmo banco, as mesmas dependências de runtime e os mesmos
testes de aceitação.

## Métricas previstas

| Dimensão    | Métricas                                                    |
| ----------- | ----------------------------------------------------------- |
| Desempenho  | latência P50/P95/P99, vazão, taxa de erro, CPU, memória     |
| Estrutura   | Ce/Ca, ciclos, CBO, LCOM, CC, cognitiva, MI (com ressalvas) |
| Evolução    | tempo de mudança, arquivos tocados, retrabalho, defeitos    |
| Testes      | cobertura de linha/ramo, mutation score                     |
| Compreensão | tempo de leitura/correção, acertos, carga subjetiva         |
| Operação    | startup, dependências, configuração, deploy                 |

## Critério de decisão

Não haverá “vencedor” único. O resultado será um **perfil de trade-offs**:

- SOLAR tende a favorecer isolamento de regras e governança;
- Clean Architecture tende a favorecer independência de frameworks;
- MVC tende a favorecer simplicidade e velocidade inicial;
- Hexagonal tende a favorecer isolamento de portas/adaptadores.

Essas são **hipóteses**, não conclusões. O benchmark existe para testá-las.

## O que não foi feito

Nenhum resultado foi inventado. Não há tabela de latência comparativa, nem
gráfico, nem ranking. Qualquer número apresentado como comparativo sem a
execução do plano seria fabricação.
