# Resumo — Etapa 5: segurança e isolamento

## Execução

| Indicador                    | Valor                                                     |
| ---------------------------- | --------------------------------------------------------- |
| Testes HTTP                  | **33**                                                    |
| Status 200                   | 2                                                         |
| Status 201                   | 8                                                         |
| Status 400                   | 18                                                        |
| Status 500                   | 5                                                         |
| Vulnerabilidades confirmadas | **0** nos cenários testados                               |
| Riscos potenciais            | endpoint público, sem tipo/tamanho, sem auth              |
| Configurações suspeitas      | CSRF/rate/brute inativos, 404/405 → 500, debug/bind amplo |

## Controles que funcionam

| Controle                                 | Evidência                                          |
| ---------------------------------------- | -------------------------------------------------- |
| Headers `nosniff`, `DENY`, `no-referrer` | presentes em 200, 201, 400 e 500                   |
| Erro genérico                            | apenas `code`, `message`, `reference`              |
| bcrypt                                   | hash `$2...` no banco; senha não retornada         |
| Validação de presença                    | 400 `MISSING_FIELDS`                               |
| Validação de JSON                        | 400 `INVALID_JSON_BODY`                            |
| Normalização                             | e-mail persistido em minúsculas                    |
| Mass assignment                          | campos extras ignorados                            |
| SQL injection                            | payload literal; tabela intacta; ORM parametrizada |

## Riscos e configurações suspeitas

| ID            | Severidade   | Achado                                       |
| ------------- | ------------ | -------------------------------------------- |
| SEC-AUTH-01   | média        | criação de usuário pública, sem autenticação |
| SEC-AUTH-02   | baixa        | senha de 1 caractere aceita                  |
| SEC-INPUT-01  | baixa        | tipo numérico em `email`/`senha` causa 500   |
| SEC-INPUT-02  | média        | sem limite de corpo/campo (64 KiB aceito)    |
| SEC-PROT-01   | baixa        | CSRF inativo                                 |
| SEC-PROT-02   | baixa        | rate limit/brute force inativos              |
| SEC-ERROR-01  | baixa        | 404/405 viram 500                            |
| SEC-CONFIG-01 | média        | debug/`0.0.0.0`/credencial DEV               |
| SEC-CONFIG-02 | baixa        | CSP/HSTS/CORS ausentes                       |
| SEC-CONFIG-03 | baixa        | header `Server` expõe versões                |
| SEC-SECRET-01 | baixa        | credencial padrão de desenvolvimento         |
| SEC-LOG-01    | média        | falha de log do Observatory sob concorrência |
| SEC-XSS-01    | inconclusivo | script armazenado; depende do consumidor     |
| SEC-JWT-01    | bloqueado    | módulo JWT sem dependência e inativo         |

## O que os dados **não** sustentam

| Afirmação                               | Por que não                                                          |
| --------------------------------------- | -------------------------------------------------------------------- |
| “A aplicação é segura.”                 | Não houve teste de penetração nem scanner externo.                   |
| “Há SQL injection.”                     | O ORM parametrizou; o payload ficou literal.                         |
| “A aplicação está isolada.”             | É o mesmo processo Python; não há isolamento de processo/permissões. |
| “O endpoint público é vulnerabilidade.” | Não há requisito formal; é risco de exposição.                       |
| “XSS é confirmado.”                     | Depende do consumidor; o JSON devolveu texto literal.                |

## Evidência principal

- `dados/RESULTADOS_TESTES.json`
- `dados/REGISTRO_ACHADOS.json`
- `evidencias/INVENTARIO_CONTROLES.md`
- `evidencias/RELATORIO_ETAPA_5_EXECUCAO.md`
