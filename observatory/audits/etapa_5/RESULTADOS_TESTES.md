# Resultados dos testes de segurança

**Execução:** 2026-10-23, aplicação local em `127.0.0.1`, SQLite temporário.  
**Dados:** sintéticos; nenhuma credencial real.  
**Resultado bruto:** [`RESULTADOS_TESTES.json`](RESULTADOS_TESTES.json).

---

## 1. Resumo

| Status HTTP | Quantidade |
| ----------- | ---------- |
| 200         | 2          |
| 201         | 8          |
| 400         | 18         |
| 500         | 5          |
| **Total**   | **33**     |

Os cinco 500 incluem dois erros de tipo (D9/D10) e três respostas de `HTTPException` mapeadas incorretamente (A2/A4/C3). Nenhuma resposta continha stack trace, caminho interno ou senha.

## 2. Tabela dos testes

| ID     | Categoria    | Teste                                | Status | Código/observação                               |
| ------ | ------------ | ------------------------------------ | ------ | ----------------------------------------------- |
| A1     | configuração | `GET /solar/health`                  | 200    | health público; headers obrigatórios presentes  |
| A2     | erro         | `GET /nao-existe`                    | 500    | code=404 no corpo; status deveria ser 404       |
| A3     | configuração | `OPTIONS /solar/health` com `Origin` | 200    | sem `Access-Control-Allow-Origin`               |
| A4     | método       | `PUT /solar/health`                  | 500    | code=405 no corpo; status deveria ser 405       |
| B1     | entrada      | criação válida                       | 201    | resposta sem senha/hash; banco com hash bcrypt  |
| C1     | autenticação | `POST` sem credencial                | 201    | endpoint público                                |
| C2     | autenticação | `POST` com `Bearer` inválido         | 201    | credencial ignorada                             |
| C3     | autorização  | `GET /examples/users/1`              | 500    | code=404; rota não existe                       |
| D1     | entrada      | `{}`                                 | 400    | `MISSING_FIELDS`                                |
| D2     | entrada      | campos só com espaços                | 400    | `MISSING_FIELDS`                                |
| D3     | entrada      | campos `null`                        | 400    | `MISSING_FIELDS`                                |
| D4     | entrada      | e-mail sem `@`                       | 400    | `INVALID_EMAIL`                                 |
| D5     | entrada      | e-mail duplicado                     | 400    | `EMAIL_TAKEN`                                   |
| D6     | entrada      | JSON malformado                      | 400    | `INVALID_JSON_BODY`                             |
| D7     | entrada      | JSON lista                           | 400    | `INVALID_JSON_BODY`                             |
| D8     | entrada      | `Content-Type: text/plain`           | 400    | `INVALID_JSON_BODY`                             |
| D9     | entrada      | `senha=123`                          | 500    | `INTERNAL_ERROR`; tipo não validado             |
| D10    | entrada      | `email=123`                          | 500    | `INTERNAL_ERROR`; tipo não validado             |
| D11    | entrada      | senha `"x"`                          | 201    | sem política de senha                           |
| D12    | entrada      | nome de 64 KiB                       | 201    | sem limite de tamanho observado                 |
| E1     | entrada      | campos extras/protegidos             | 201    | id gerado 6; `reset_password=false`; data atual |
| E2     | entrada      | payload SQL no nome                  | 201    | nome armazenado literal; tabela intacta         |
| E3     | entrada      | `<script>` no nome                   | 201    | retornado literalmente em JSON                  |
| F1–F10 | proteção     | 10 tentativas inválidas              | 400    | nenhuma resposta 429; sem rate limit            |

## 3. Evidências de banco

| Verificação                                     | Resultado                                       |
| ----------------------------------------------- | ----------------------------------------------- |
| Registro de B1                                  | encontrado; id 1                                |
| Senha em texto no banco                         | **não**                                         |
| Hash bcrypt                                     | **sim** (`$2...`)                               |
| Campo extra `id_user=999999` aplicado           | **não**; id gerado 6                            |
| Campo extra `reset_password_user=true` aplicado | **não**; permaneceu `false`                     |
| Payload SQL executado                           | **não**; nome literal e tabela `users` presente |
| Total de usuários ao final                      | 8 (dados sintéticos)                            |

## 4. Cabeçalhos observados

Presentes em 200, 201, 400 e 500:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`

Ausentes por padrão:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `Access-Control-Allow-Origin`

Também foi observado `Server: Werkzeug/3.1.9 Python/3.14.7`.

## 5. O que os testes demonstram — e o que não demonstram

**Demonstram:**

- o endpoint de criação é público e não exige CSRF;
- validação de presença funciona, mas tipo e tamanho não;
- hash bcrypt e proteção contra campos extras funcionam;
- payload SQL não foi executado;
- headers obrigatórios e mensagens genéricas funcionam;
- 404/405 são mascarados como 500;
- não há rate limit em 10 tentativas inválidas.

**Não demonstram:**

- exploração de XSS sem um frontend consumidor;
- IDOR, pois não há rota por identificador;
- eficácia de CSRF/rate limit/brute force, pois não estão ativos;
- comportamento em PostgreSQL;
- exposição de rede ou de produção;
- ausência geral de vulnerabilidades.

## 6. Achados

A classificação completa, com impacto, severidade, limitações e recomendação, está em [`REGISTRO_ACHADOS.json`](REGISTRO_ACHADOS.json). Resumo:

| ID            | Status                | Severidade | Achado                                        |
| ------------- | --------------------- | ---------- | --------------------------------------------- |
| SEC-AUTH-01   | risco potencial       | média      | criação de usuário pública                    |
| SEC-AUTH-02   | risco potencial       | baixa      | senha de 1 caractere aceita                   |
| SEC-AUTHZ-01  | não aplicável         | —          | sem autorização/IDOR no conjunto atual        |
| SEC-INPUT-01  | risco potencial       | baixa      | tipo numérico causa 500                       |
| SEC-INPUT-02  | risco potencial       | média      | sem limite de tamanho de corpo/campo          |
| SEC-PROT-01   | configuração suspeita | baixa      | CSRF inativo                                  |
| SEC-PROT-02   | configuração suspeita | baixa      | rate limit/brute force inativos               |
| SEC-ERROR-01  | configuração suspeita | baixa      | 404/405 viram 500                             |
| SEC-CONFIG-01 | configuração suspeita | média      | debug/0.0.0.0/credencial DEV                  |
| SEC-CONFIG-02 | configuração suspeita | baixa      | CSP/HSTS/CORS não aplicados                   |
| SEC-CONFIG-03 | configuração suspeita | baixa      | header Server expõe versões                   |
| SEC-SECRET-01 | configuração suspeita | baixa      | credencial padrão de desenvolvimento          |
| SEC-JWT-01    | bloqueado             | —          | módulo JWT sem dependência e inativo          |
| SEC-LOG-01    | risco potencial       | média      | falha de log do Observatório sob concorrência |
| SEC-XSS-01    | inconclusivo          | —          | script armazenado; depende do consumidor      |
| SEC-SQLI-01   | controle validado     | —          | ORM parametrizada                             |
| SEC-MASS-01   | controle validado     | —          | campos extras ignorados                       |
