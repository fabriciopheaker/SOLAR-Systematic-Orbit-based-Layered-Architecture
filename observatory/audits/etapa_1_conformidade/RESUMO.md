# Resumo — Etapa 1: conformidade

## Resultado

| Indicador                       | Valor                                     |
| ------------------------------- | ----------------------------------------- |
| Verificações executadas         | **17**                                    |
| Regras aplicadas pelo `check`   | **29**                                    |
| Violações                       | **0**                                     |
| Regras violadas                 | **0**                                     |
| Códigos de regra no catálogo    | **30**                                    |
| Regras sem verificação estática | **1** (`SOLAR-ROF-003`)                   |
| Regra absorvida                 | **1** (`SOLAR-RED-004` → `SOLAR-RED-001`) |

**Conclusão curta:** o código atual passa em todas as regras que o
`ProjectValidator` consegue verificar. Isso **não** equivale a “100% conforme”,
porque a ROF-003 não é executada pelo comando `check`.

## A correção sobre a ROF-003

A frase “a ROF-003 não é executada” precisa de qualificador. O que os
artefatos mostram:

1. **Não é executada pelo `ProjectValidator`:** a classe
   `ControllerAndUseCaseMustUseNamedContracts` existe, mas não aparece em
   `project_checks()`.
2. **É exercitada por testes unitários:** há teste específico em
   `observatory/tests/rules/architecture/test_controller_and_usecase_must_use_named_contracts.py`.
3. **Não é uma regra de persistência:** a ROF-003 trata de contratos nomeados
   de entrada/saída de Controllers e UseCases. A organização
   Model → Persistence → Repository é verificada pelas regras RED-002,
   RED-003, RED-005, RED-006, RED-007 e RED-008, todas executadas.

Portanto, a conclusão correta é: **a conformidade é parcial apenas porque falta
verificação estática da ROF-003**, não porque a persistência esteja fora do
lugar. A estrutura observada confirma um Model por arquivo, uma Persistence
para o Model de usuário e Repositories que dependem da Persistence
correspondente.

## Evidência principal

- `evidencias/check/check-2026-10-23-124423-correct.md`
- Saída do comando: **17 verificações**, **29 regras**, **0 violações**.

## Limitações

- O `check` não mede se as regras são eficazes; mede se o código atual as
  satisfaz.
- A ROF-003 só é verificada quando o contrato é submetido à Rule; não há
  varredura automática dos Controllers/UseCases do projeto.
- O escopo do `check` exclui testes, exemplos e diretórios técnicos; a
  conformidade dos testes não é avaliada.
