# Dados do benchmark

**Este diretório está intencionalmente vazio de resultados.**

Não há dados comparativos porque as implementações Clean Architecture, MVC e
Hexagonal do mesmo sistema de referência não existem neste repositório, e não
há harness comum nem ambiente controlado para as quatro.

## Regra de integridade

1. Nenhum número comparativo pode ser criado sem execução real.
2. Cada resultado deve ter:
   - commit SHA da implementação;
   - comando exato;
   - versões de Python e bibliotecas;
   - hardware e sistema;
   - seed e dataset;
   - arquivo bruto por requisição;
   - data e operador.
3. Resultados de uma arquitetura não podem ser comparados com resultados de
   outra obtidos em ambiente diferente.
4. MI não pode ser usado como ranking de manutenibilidade.
5. Uma execução não é um benchmark; o mínimo é ≥ 5 repetições por célula.

Enquanto a fase 0 do plano não for concluída, este diretório deve permanecer
sem resultados.
