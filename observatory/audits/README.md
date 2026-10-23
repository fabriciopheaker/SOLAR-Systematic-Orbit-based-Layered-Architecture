# `observatory/audits` — índice geral da auditoria

Esta pasta concentra **todos os artefatos de análise e auditoria** da SOLAR.
Ela é organizada em seis etapas uniformes e um estudo de benchmark. Cada etapa
tem o mesmo contrato documental:

- `README.md` — escopo, artefatos e reprodução;
- `RESUMO.md` — resposta curta, números e limites;
- `RELATORIO_TECNICO.md` — método, resultados, interpretação e limitações.

## As seis etapas

| Etapa                                     | Pergunta                                      | Status                                            | Documento                                                                                     |
| ----------------------------------------- | --------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **1. Conformidade**                       | as regras declaradas são obedecidas?          | concluída para 29 regras; **parcial** na ROF-003  | [`etapa_1_conformidade/`](etapa_1_conformidade/README.md)                                     |
| **2. Acoplamento, coesão e dependências** | como os módulos dependem uns dos outros?      | concluída, com ressalvas                          | [`etapa_2_acoplamento_coesao/`](etapa_2_acoplamento_coesao/README.md)                         |
| **3. Complexidade**                       | onde está o custo de leitura/decisão?         | concluída, com limitações de métrica              | [`etapa_3_complexidade/`](etapa_3_complexidade/README.md)                                     |
| **4. Desempenho**                         | como a aplicação se comporta sob carga?       | concluída; 12 cenários, 1.860 requisições         | [`etapa_4_desempenho/`](etapa_4_desempenho/README.md)                                         |
| **5. Segurança e isolamento**             | quais controles existem e quais estão ativos? | concluída; 33 testes HTTP                         | [`etapa_5_seguranca_isolamento/`](etapa_5_seguranca_isolamento/README.md)                     |
| **6. Manutenibilidade e evolutividade**   | a arquitetura ajuda ou dificulta mudanças?    | **preliminar**; estudo longitudinal não executado | [`etapa_6_manutenibilidade_evolutividade/`](etapa_6_manutenibilidade_evolutividade/README.md) |

## Estudo de benchmark

| Estudo                                       | Status                                                | Documento                           |
| -------------------------------------------- | ----------------------------------------------------- | ----------------------------------- |
| SOLAR × Clean Architecture × MVC × Hexagonal | **plano e viabilidade; nenhuma execução comparativa** | [`benchmark/`](benchmark/README.md) |

O benchmark **não contém resultados inventados**. A ausência de implementações
equivalentes e de ambiente controlado está documentada em
[`benchmark/RELATORIO_TECNICO.md`](benchmark/RELATORIO_TECNICO.md).

## Resumo executivo

O documento de síntese é [`RESUMO_EXECUTIVO.md`](RESUMO_EXECUTIVO.md). Ele
responde, em uma página, o que os dados sustentam, o que não sustentam e quais
são as pendências.

## Estrutura

```text
observatory/audits/
├── README.md                         # este índice
├── RESUMO_EXECUTIVO.md               # síntese geral
├── etapa_1_conformidade/
│   ├── README.md
│   ├── RESUMO.md
│   ├── RELATORIO_TECNICO.md
│   └── evidencias/check/             # histórico do comando check
├── etapa_2_acoplamento_coesao/
│   ├── README.md, RESUMO.md, RELATORIO_TECNICO.md
│   ├── dados/                        # CSVs/JSONs canônicos
│   ├── scripts/                      # solar_metrics.py, revisar_relatorio.py
│   └── evidencias/                   # auditoria, checklist, tracing
├── etapa_3_complexidade/
│   ├── README.md, RESUMO.md, RELATORIO_TECNICO.md
│   ├── dados/                        # CC, cognitiva, Halstead, Radon bruto
│   └── evidencias/                   # auditoria da etapa
├── etapa_4_desempenho/
│   ├── README.md, RESUMO.md, RELATORIO_TECNICO.md
│   ├── PLANO_DE_TESTES.md
│   ├── dados/                        # consolidado, brutos, startup, tmp
│   ├── scripts/                      # benchmark e diagnóstico
│   └── evidencias/                   # relatório original
├── etapa_5_seguranca_isolamento/
│   ├── README.md, RESUMO.md, RELATORIO_TECNICO.md
│   ├── PLANO_DE_TESTES.md
│   ├── dados/                        # resultados, achados, startup, tmp
│   ├── scripts/                      # executor e servidor isolado
│   └── evidencias/                   # inventário e relatório original
├── etapa_6_manutenibilidade_evolutividade/
│   ├── README.md, RESUMO.md, RELATORIO_TECNICO.md
│   └── dados/LEIA-ME.md              # nenhum dado novo: protocolo planejado
└── benchmark/
    ├── README.md, RESUMO.md
    ├── PLANO_DE_BENCHMARK.md
    ├── RELATORIO_TECNICO.md
    └── dados/LEIA-ME.md              # intencionalmente sem resultados
```

## Relação com o corpus de produção

Os scripts desta pasta são **ferramentas de observação**, não módulos da
aplicação. `solar_metrics.py` e `verificacoes_independentes.py` excluem
`observatory/audits/` e `observatory/tests/` do corpus de produção. A contagem
de **208 módulos, 306 arestas e 553 funções** continua sendo a do código da
aplicação, sem os instrumentos de auditoria.

O `ProjectValidator` continua varrendo os arquivos `.py` desta pasta para
garantir que as próprias ferramentas respeitem as regras arquiteturais.

## Comandos de reprodução

```powershell
# Etapa 1 — conformidade
py observatory/solar check

# Etapas 2 e 3 — acoplamento, coesão e complexidade
py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py
py observatory/audits/etapa_2_acoplamento_coesao/scripts/revisar_relatorio.py
py observatory/audits/etapa_2_acoplamento_coesao/evidencias/verificacoes_independentes.py

# Etapa 4 — desempenho
py observatory/audits/etapa_4_desempenho/scripts/run_benchmark.py
py observatory/audits/etapa_4_desempenho/scripts/diagnose_concurrency.py

# Etapa 5 — segurança
py observatory/audits/etapa_5_seguranca_isolamento/scripts/run_security_tests.py
```

## Regra de integridade

1. Nenhum resultado é inventado.
2. O que não foi medido está marcado como **planejado** ou **não executado**.
3. Cada número tem arquivo de origem e comando de reprodução.
4. A etapa 6 e o benchmark são declarações de limite, não promessas.
