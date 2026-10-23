# Etapa 6 — Manutenibilidade e evolutividade

**Pergunta:** a arquitetura atual ajuda ou dificulta mudanças futuras?

**Status:** **avaliação preliminar concluída; estudo longitudinal não executado.**
Esta etapa reúne a evidência existente sobre manutenibilidade e define o
protocolo necessário para uma conclusão mais forte. Não há resultado inventado:
o que não foi medido está marcado como **planejado**.

## Artefatos

| Artefato                                       | Conteúdo                                              |
| ---------------------------------------------- | ----------------------------------------------------- |
| [`RESUMO.md`](RESUMO.md)                       | o que já se pode dizer e o que falta                  |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md) | evidência existente, limites e protocolo de avaliação |
| [`dados/LEIA-ME.md`](dados/LEIA-ME.md)         | por que não há dados novos nesta etapa                |

## O que já existe

- MI do Radon reproduzido em 269/269 módulos, com **0 divergências**;
- MI de produção: 208/208 rank A, média 88,14, mediana 100;
- **110 de 208** módulos de produção com MI 100;
- sensibilidade a docstrings: 26 módulos com delta > 10 pontos;
- 15 módulos fora do fluxo estático (631 SLOC);
- suíte de testes existente, mas **cobertura e mutação não medidas**;
- uma única fotografia do código, sem histórico de mudanças.

## O que falta para concluir

| Dimensão                   | Medida necessária                 | Status        |
| -------------------------- | --------------------------------- | ------------- |
| Manutenibilidade percebida | estudo com mantenedores           | **planejado** |
| Evolutividade              | cenários de mudança cronometrados | **planejado** |
| Cobertura de testes        | cobertura de linha/ramo           | **planejado** |
| Qualidade dos testes       | mutation score                    | **planejado** |
| Acoplamento de mudança     | change coupling por commit        | **planejado** |
| Tendência                  | série histórica                   | **planejado** |
| Dependências               | idade, CVEs, atualidade           | **planejado** |

## Leitura de uma frase

O MI **não discrimina** (110 módulos em 100), então ele não sustenta a frase “o
código é fácil de manter”. A estrutura observada é compatível com evolução
modular, mas **evolutividade não foi medida**. A conclusão honesta é:
**plausível, não demonstrada**.
