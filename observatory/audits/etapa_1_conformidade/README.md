# Etapa 1 — Conformidade arquitetural

**Pergunta:** as regras declaradas da SOLAR são obedecidas pelo código atual?

**Status:** concluída para as 29 regras com verificação estática; **parcial** para a ROF-003, que não possui scanner no `ProjectValidator`.

## Artefatos

| Artefato                                                                                                     | Conteúdo                                              |
| ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| [`RESUMO.md`](RESUMO.md)                                                                                     | resposta curta, números e ressalva da ROF-003         |
| [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md)                                                               | método, inventário de regras, evidências e limitações |
| [`evidencias/check/check-2026-10-23-124423-correct.md`](evidencias/check/check-2026-10-23-124423-correct.md) | execução mais recente do comando `check`              |
| [`evidencias/check/`](evidencias/check/)                                                                     | histórico de verificações arquiteturais               |

## Reprodução

```powershell
py observatory/solar check
```

O comando executa 17 verificações sobre 29 regras, grava o relatório em
`observatory/audits/etapa_1_conformidade/evidencias/check/` e devolve código
de saída `0` quando não há violação.

## O que esta etapa não prova

- Não prova conformidade total: a `SOLAR-ROF-003` é implementada e testada
  unitariamente, mas não é executada pelo `ProjectValidator`.
- Não mede comportamento em runtime; isso pertence às etapas 4 e 5.
- Não mede qualidade global; isso pertence às etapas 2, 3 e 6.
