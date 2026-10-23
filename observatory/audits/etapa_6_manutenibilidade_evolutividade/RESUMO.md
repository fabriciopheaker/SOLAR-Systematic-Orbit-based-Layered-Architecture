# Resumo — Etapa 6: manutenibilidade e evolutividade

## Status

**Preliminar.** Não houve estudo longitudinal, nem estudo com mantenedores, nem
medição de cobertura/mutação. Qualquer afirmação forte sobre manutenibilidade
seria opinião, não resultado.

## Evidência existente

| Indicador                      | Valor                                    | Interpretação                 |
| ------------------------------ | ---------------------------------------- | ----------------------------- |
| MI reproduzido                 | 269/269, 0 divergências                  | fórmula e dados confiáveis    |
| MI de produção                 | 208/208 rank A                           | **não discrimina**            |
| MI médio de produção           | 88,14                                    | alto, mas saturado            |
| MI mediano de produção         | 100                                      | metade no teto                |
| Módulos com MI 100             | **110 de 208 (52,9%)**                   | saturação                     |
| Sensibilidade a docstrings     | 26 módulos com delta > 10; máximo +47,62 | MI é sensível a comentários   |
| Módulos fora do fluxo estático | 15 (631 SLOC)                            | possível dívida de integração |
| Suíte de testes                | **587 testes passando** (2026-10-23)     | presença de suíte             |
| Cobertura de testes            | não medida                               | lacuna                        |
| Mutation score                 | não medido                               | lacuna                        |
| Histórico de mudanças          | uma fotografia                           | lacuna                        |

## O que os dados sustentam

1. **O MI não serve como ranking** nesta base: metade dos módulos está no teto.
2. **A saturação tem causa:** volume Halstead zero por limitação do Radon e
   docstrings contadas como comentário.
3. **Há superfície não exercitada:** 15 módulos fora do fluxo estático.
4. **A estrutura é compatível com evolução modular:** baixo acoplamento e
   separação por camadas.
5. **Nada disso prova facilidade de manutenção:** não há evidência empírica de
   mudanças, defeitos ou esforço de manutenção.

## O que os dados **não** sustentam

| Afirmação                     | Por que não                                       |
| ----------------------------- | ------------------------------------------------- |
| “O código é fácil de manter.” | MI saturado; não há estudo com mantenedores.      |
| “A dívida técnica é baixa.”   | Não há série histórica nem análise de mudanças.   |
| “A arquitetura evolui bem.”   | Evolutividade não foi medida.                     |
| “Os testes cobrem o sistema.” | Cobertura e mutação não foram medidas.            |
| “O MI 100 é perfeito.”        | É ausência de volume/complexidade, não qualidade. |

## Protocolo mínimo para concluir

1. **Cenários de mudança** (5–8 tarefas equivalentes, cronometradas):
   adicionar campo, endpoint, validação, persistência, autenticação e nova regra.
2. **Métricas de processo:** lead time, arquivos tocados, retrabalho, defeitos
   pós-merge.
3. **Cobertura + mutação:** linha/ramo e mutation score por módulo crítico.
4. **Change coupling:** co-mudança por commit (janela de 6–12 meses).
5. **Estudo com mantenedores:** tempo de compreensão e correção.
6. **Série histórica:** pelo menos 3 pontos no tempo.

## Veredito

| Afirmação                    | Veredito                       |
| ---------------------------- | ------------------------------ |
| O MI é alto                  | **sustentada** (mas saturado)  |
| O MI mede manutenibilidade   | **não sustentada**             |
| A arquitetura é evolutiva    | **não demonstrada**            |
| Há dívida técnica crescente  | **não sustentada** (sem série) |
| Há superfície não exercitada | **sustentada** (15 módulos)    |
