# Relatório — Etapa 5: segurança e isolamento

**Projeto:** SOLAR  
**Data:** 2026-10-23  
**Ambiente:** Windows 11, Python 3.14.7, Flask 3.1.3, SQLite temporário, `127.0.0.1`  
**Artefatos:** [`PLANO_DE_TESTES.md`](PLANO_DE_TESTES.md), [`INVENTARIO_CONTROLES.md`](INVENTARIO_CONTROLES.md), [`RESULTADOS_TESTES.md`](RESULTADOS_TESTES.md), [`REGISTRO_ACHADOS.json`](REGISTRO_ACHADOS.json)  
**Código de produção:** não alterado.

---

## 1. Resumo executivo

Foram executados **33 testes HTTP** com dados sintéticos contra a aplicação isolada. Os resultados mostram:

1. **Os três headers de segurança obrigatórios** (`nosniff`, `DENY`, `no-referrer`) foram aplicados em respostas 200, 201, 400 e 500.
2. **A validação de presença e a sanitização JSON funcionam**, mas **não há validação de tipo nem limite de tamanho**. Tipos numéricos em `email`/`senha` geram **500**; um nome de **64 KiB** foi aceito e gravado.
3. **O endpoint `POST /examples/users` é público**: respondeu **201** sem credencial e com `Authorization: Bearer` inválido. Não há autenticação nem autorização implementadas no caminho HTTP.
4. **Não há CSRF, rate limit ou brute force ativos**, apesar de as classes existirem. Dez tentativas inválidas retornaram 400, sem 429.
5. **A injeção SQL testada não foi executada**: o payload ficou literal e a tabela permaneceu íntegra; o ORM usa consultas parametrizadas.
6. **Campos extras/protegidos foram ignorados**: `id_user`, `reset_password_user` e `data_created_user` enviados no JSON não alteraram o registro.
7. **Erros 404/405 são mascarados como 500** pelo handler global, embora o corpo preserve `code=404/405`.
8. **O hash bcrypt e a não exposição da senha** foram confirmados no banco e na resposta.

**Vulnerabilidades confirmadas:** nenhuma nos cenários testados.  
**Riscos potenciais:** endpoint público de escrita, ausência de limites de entrada, ausência de autenticação/autorização, controles de proteção inativos, configuração de desenvolvimento exposta e falha de observabilidade sob concorrência.

---

## 2. Escopo e método

### 2.1 Componentes inspecionados

- `nucleus/kernel.py` — montagem e ativação dos mecanismos.
- `nucleus/security/` — `json_validator`, `json_sanitizer`, `password`, `identity`, `token`, `url_guard`, `attempt_tracker`.
- `nucleus/middleware/` — `request_pipeline`, `solar_blueprint`, `atmosphere`, `security_headers`, `security_policy`, `csrf_protection`, `rate_limiter`, `brute_force_guard`, `error_handler`.
- `nucleus/upload/` — sanitização/validação de arquivos (sem rota).
- `orbits/planets/example/` — rota, Controller, Sanitizer, Validator, UseCase, Repository, Entity, Resource.
- `orbits/planets/solar/` — rota de saúde.
- `orbits/planets/auth/` e `user/` — Blueprints sem rotas.
- `orbits/database/` — Model, Persistence, Repository.
- `server.py`, `nucleus/.env`, `docker/docker-compose.yml`, `.gitignore`.
- Testes existentes em `tests/security`, `tests/middleware` e `tests/orbits`.

### 2.2 Método

1. Inspeção estática de rotas, imports, instanciação e configuração.
2. Verificação de testes existentes (`pytest`).
3. Execução da aplicação em processo separado, SQLite temporário, `.env` temporário e storage temporário.
4. Testes HTTP com dados sintéticos, sem carga, sem concorrência e sem ações destrutivas.
5. Leitura direta do SQLite temporário para confirmar hash, campos e integridade.
6. Classificação e redação de achados sem valores secretos.

### 2.3 Ferramentas

| Item            | Versão/uso                                                |
| --------------- | --------------------------------------------------------- |
| Python          | 3.14.7                                                    |
| Flask           | 3.1.3                                                     |
| Werkzeug        | 3.1.9 (servidor de teste)                                 |
| SQLAlchemy      | 2.1.1                                                     |
| bcrypt          | 5.0.0                                                     |
| pytest          | 9.1.1                                                     |
| Cliente HTTP    | `http.client` da stdlib                                   |
| Scanner externo | **não utilizado**; a análise foi manual + testes próprios |

**Não foi usado** Sonar, Bandit, OWASP ZAP, Burp ou scanner de segredos. A ausência de scanner não é compensada por testes manuais; é uma limitação declarada.

---

## 3. Categorias avaliadas

| Categoria            | O que foi feito                                                                        | Resultado                                                                           |
| -------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **A — Autenticação** | Inspeção de rotas/middleware; POST sem credencial e com Bearer inválido                | não implementada; endpoint público (C1/C2)                                          |
| **B — Autorização**  | Busca por papéis/permissões; tentativa de acesso por ID                                | não implementada; não há rota por ID para testar IDOR (C3)                          |
| **C — Isolamento**   | Inspeção de imports, estado global, `Database` e limites de processo                   | não há isolamento real de processo/permissões; mesmo processo Python                |
| **D — Entrada**      | Corpo vazio, branco, nulo, inválido, duplicado, malformado, lista, tipo errado, 64 KiB | presença e JSON validados; tipo e tamanho não                                       |
| **E — Segredos**     | Inspeção de `.env`, compose, respostas, erros e banco                                  | sem segredo real versionado; credencial DEV no compose; sem vazamento nas respostas |
| **F — Comunicação**  | Busca por Satellites, clientes HTTP e integrações                                      | não aplicável; não existe no código atual                                           |
| **G — Configuração** | Headers, CORS, debug, host/porta, banco, permissões                                    | 3 headers ativos; CSP/HSTS/CORS ausentes; DEV com debug e bind amplo                |
| **H — Proteção**     | Onde cada mecanismo é definido/instanciado/executado                                   | 5 ativos; CSRF/rate/brute/URL/JWT/upload inativos                                   |

---

## 4. Testes dinâmicos

A tabela completa está em [`RESULTADOS_TESTES.md`](RESULTADOS_TESTES.md); o JSON bruto em [`RESULTADOS_TESTES.json`](RESULTADOS_TESTES.json).

### 4.1 Resultados por status

| Status    | Quantidade | Observação                                                   |
| --------- | ---------- | ------------------------------------------------------------ |
| 200       | 2          | health e OPTIONS                                             |
| 201       | 8          | criações válidas/extras/SQL/XSS/senha curta/64 KiB           |
| 400       | 18         | validações, duplicidade, JSON inválido, tentativas inválidas |
| 500       | 5          | 2 tipos errados + 3 HTTPException mascaradas                 |
| **Total** | **33**     |                                                              |

### 4.2 Casos principais

| ID     | Teste                                     | Resultado observado                    | Interpretação                       |
| ------ | ----------------------------------------- | -------------------------------------- | ----------------------------------- |
| A1     | health                                    | 200, JSON, 3 headers                   | rota pública e funcional            |
| A2     | rota inexistente                          | **500**, code=404                      | erro de cliente mascarado           |
| A3     | OPTIONS com Origin                        | 200, sem ACAO                          | CORS não habilitado                 |
| A4     | método não permitido                      | **500**, code=405                      | erro de cliente mascarado           |
| B1     | criação válida                            | 201, sem senha/hash; banco com `$2...` | hash bcrypt; resposta segura        |
| C1     | POST sem credencial                       | 201                                    | endpoint público                    |
| C2     | POST com Bearer inválido                  | 201                                    | credencial ignorada                 |
| C3     | GET por ID                                | **500**, code=404                      | rota inexistente; sem IDOR testável |
| D1–D3  | vazio/branco/nulo                         | 400 `MISSING_FIELDS`                   | validação de presença funciona      |
| D4     | e-mail inválido                           | 400 `INVALID_EMAIL`                    | regra de domínio funciona           |
| D5     | e-mail duplicado                          | 400 `EMAIL_TAKEN`                      | consulta e regra funcionam          |
| D6–D8  | JSON malformado/lista/content-type errado | 400 `INVALID_JSON_BODY`                | guarda de entrada funciona          |
| D9     | `senha=123`                               | **500** `INTERNAL_ERROR`               | tipo não validado                   |
| D10    | `email=123`                               | **500** `INTERNAL_ERROR`               | tipo não validado                   |
| D11    | senha `"x"`                               | 201                                    | sem política de senha               |
| D12    | nome de 64 KiB                            | 201                                    | sem limite de tamanho               |
| E1     | campos extras/protegidos                  | 201; id 6; reset=false                 | sem mass assignment                 |
| E2     | payload SQL no nome                       | 201; nome literal; tabela intacta      | ORM parametrizada                   |
| E3     | `<script>` no nome                        | 201; texto literal em JSON             | depende do consumidor               |
| F1–F10 | 10 tentativas inválidas                   | 400, sem 429                           | sem rate limit                      |

### 4.3 Verificação no banco

| Verificação                         | Resultado                        |
| ----------------------------------- | -------------------------------- |
| Senha em texto no banco             | não                              |
| Hash bcrypt                         | sim                              |
| `id_user` extra aplicado            | não (id gerado 6)                |
| `reset_password_user=true` aplicado | não (permaneceu `false`)         |
| `data_created_user` injetado        | não (data atual)                 |
| Payload SQL executado               | não                              |
| Tabela `users` após payload         | presente, 8 registros sintéticos |

---

## 5. Achados

A lista estruturada, com todos os campos exigidos, está em [`REGISTRO_ACHADOS.json`](REGISTRO_ACHADOS.json).

| ID            | Status                | Severidade | Achado                                        |
| ------------- | --------------------- | ---------- | --------------------------------------------- |
| SEC-AUTH-01   | risco potencial       | média      | criação de usuário pública, sem autenticação  |
| SEC-AUTH-02   | risco potencial       | baixa      | senha de 1 caractere aceita                   |
| SEC-AUTHZ-01  | não aplicável         | —          | sem autorização/IDOR no conjunto atual        |
| SEC-INPUT-01  | risco potencial       | baixa      | tipo numérico causa 500                       |
| SEC-INPUT-02  | risco potencial       | média      | sem limite de corpo/campo                     |
| SEC-PROT-01   | configuração suspeita | baixa      | CSRF inativo                                  |
| SEC-PROT-02   | configuração suspeita | baixa      | rate limit/brute force inativos               |
| SEC-ERROR-01  | configuração suspeita | baixa      | 404/405 viram 500                             |
| SEC-CONFIG-01 | configuração suspeita | média      | debug/0.0.0.0/credencial DEV                  |
| SEC-CONFIG-02 | configuração suspeita | baixa      | CSP/HSTS/CORS não aplicados                   |
| SEC-CONFIG-03 | configuração suspeita | baixa      | header `Server` expõe versões                 |
| SEC-SECRET-01 | configuração suspeita | baixa      | credencial padrão de desenvolvimento          |
| SEC-JWT-01    | bloqueado             | —          | módulo JWT sem dependência e inativo          |
| SEC-LOG-01    | risco potencial       | média      | falha de log do Observatório sob concorrência |
| SEC-XSS-01    | inconclusivo          | —          | script armazenado; depende do consumidor      |
| SEC-SQLI-01   | controle validado     | —          | ORM parametrizada                             |
| SEC-MASS-01   | controle validado     | —          | campos extras ignorados                       |

### 5.1 Critério de severidade

Foi usada uma escala qualitativa:

- **baixa:** impacto limitado a robustez, informação de versão ou configuração sem exposição demonstrada;
- **média:** impacto potencial em disponibilidade, integridade ou abuso de endpoint público, com exploração plausível;
- **alta:** não atribuída nesta auditoria;
- **não aplicável/bloqueado:** não há mecanismo ou dependência para testar.

Não foi aplicada pontuação CVSS formal. A severidade é uma estimativa condicionada ao ambiente local e às limitações declaradas.

---

## 6. Controles validados

| Controle                  | Evidência                                                                       |
| ------------------------- | ------------------------------------------------------------------------------- |
| Headers obrigatórios      | presentes em 200, 201, 400 e 500                                                |
| Mensagem de erro genérica | respostas com apenas `code`, `message`, `reference`; sem stack trace ou caminho |
| Hash bcrypt               | senha no banco começa com `$2` e não é texto puro                               |
| Validação de presença     | 400 `MISSING_FIELDS` para vazio, branco e nulo                                  |
| Validação de JSON         | 400 `INVALID_JSON_BODY` para malformado, lista e content-type errado            |
| Normalização              | e-mail sintético persistido em minúsculas                                       |
| Atribuição em massa       | campos extras ignorados                                                         |
| Injeção SQL               | payload armazenado literalmente; tabela intacta                                 |

---

## 7. Riscos e configurações suspeitas

### 7.1 Endpoint público de escrita

`POST /examples/users` cria usuário sem autenticação. O Planet `example` é um fluxo de referência e pode ser público por desenho; **não foi classificado como vulnerabilidade confirmada** porque não há requisito formal de proteção. O risco é real se a rota for exposta fora do ambiente local: criação de contas, abuso de recursos e ausência de responsabilização.

### 7.2 Validação insuficiente

- Tipos errados causam 500: `senha=123`, `email=123`.
- Nome de 64 KiB foi aceito.
- Senha de um caractere foi aceita.
- Não há `MAX_CONTENT_LENGTH` configurado.
- `String(100)` no Model não é aplicado pelo SQLite; em PostgreSQL, um nome maior pode falhar de forma diferente.

### 7.3 Controles inativos

- `CsrfProtection`: classe existe; `csrf_enabled=True` é inerte; não há instanciação.
- `RateLimiter` / `BruteForceGuard`: classes existem; não há middleware; 10 tentativas não geraram 429.
- `UrlGuard`: existe; não há chamada externa.
- `Token` JWT: existe; `PyJWT` não instalado; não há autenticação.
- Upload: módulos existem; não há rota.

### 7.4 Tratamento de erros

O `errorhandler(Exception)` captura `HTTPException` e devolve 500. O corpo preserva `code=404/405`, mas o status HTTP está errado. Isso afeta monitoramento, clientes e políticas de retry; não expõe detalhe interno.

### 7.5 Configuração

- `server.py` liga debug quando `APP_ENV=DEV`.
- `docker-compose.yml` usa `APP_ENV=DEV`, `DEV_HOST=0.0.0.0` e `5000:5000`.
- O compose contém credencial padrão de PostgreSQL de desenvolvimento.
- `.env` está ignorado pelo Git, mas contém `SECRET_KEY` e credenciais locais.
- CORS é lido do ambiente, mas não aplicado.
- CSP/HSTS não são configurados por padrão.
- `Server` expõe versões do Werkzeug/Python.

### 7.6 Observabilidade

A Etapa 4 mostrou **8 respostas 500 e 0 registros** em `error_log.sqlite`; o teste direto confirmou que a conexão SQLite do `ErrorLog` é criada na thread principal e usada nas threads de requisição (`sqlite3.ProgrammingError`). O `ErrorHandler` silencia a falha do observador. É uma lacuna de trilha de auditoria sob concorrência, não uma ampliação de acesso.

---

## 8. Testes não executados ou bloqueados

| Item                                | Motivo                                                   |
| ----------------------------------- | -------------------------------------------------------- |
| IDOR / autorização por proprietário | não há rota de leitura/atualização por identificador     |
| CSRF significativo                  | não há autenticação por cookie/sessão                    |
| Brute force de credenciais          | não há login                                             |
| JWT                                 | `PyJWT` não instalado; módulo inativo                    |
| PostgreSQL                          | não há instância isolada disponível                      |
| Docker                              | não há CLI Docker no Windows                             |
| Upload                              | não há rota                                              |
| Satellites/comunicação externa      | não há módulo de satélites                               |
| Scanner de vulnerabilidades         | não instalado; não era necessário para os testes diretos |
| Teste de carga/DoS                  | fora do escopo e proibido pelos limites                  |

---

## 9. Recomendações priorizadas

| Prioridade | Recomendação                                                                                | Justificativa                       |
| ---------- | ------------------------------------------------------------------------------------------- | ----------------------------------- |
| 1          | Definir se `POST /examples/users` é público; se não, exigir autenticação e autorização      | endpoint de escrita sem identidade  |
| 2          | Validar tipos e limites de tamanho no `Validator`; configurar `MAX_CONTENT_LENGTH`          | 500 por tipo e 64 KiB aceitos       |
| 3          | Corrigir o mapeamento de `HTTPException` para 404/405                                       | semântica HTTP e monitoramento      |
| 4          | Ativar CSRF/rate limit quando houver sessão/autenticação; remover flag inerte ou documentar | controles existem, mas não protegem |
| 5          | Remover debug/0.0.0.0/credencial padrão do ambiente compartilhado                           | configuração de desenvolvimento     |
| 6          | Corrigir o logging concorrente do Observatório                                              | trilha de auditoria                 |
| 7          | Definir política de senha quando houver login                                               | senha de 1 caractere aceita         |
| 8          | Adicionar CSP/HSTS quando houver frontend/TLS                                               | defesa em profundidade              |
| 9          | Documentar a política CORS e testar o frontend                                              | configuração não aplicada           |
| 10         | Adicionar testes automatizados para tipos, limites, 404/405 e auth                          | regressão                           |

---

## 10. Limitações

- Aplicação local, SQLite, servidor de desenvolvimento Werkzeug; não representa produção.
- Sem autenticação/login, não foi possível testar brute force, CSRF ou JWT em uso.
- Sem frontend, XSS ficou inconclusivo.
- Sem PostgreSQL e Docker, diferenças de configuração/DB não foram medidas.
- A análise de segredos foi manual, sem scanner de histórico Git.
- Não foi executada análise de dependências/CVE nesta etapa.
- Não houve teste de carga; a observação de concorrência vem da Etapa 4.
- A ausência de achados não prova ausência de vulnerabilidades.

---

## 11. Verificação final

| Item                                      | Resultado                                           |
| ----------------------------------------- | --------------------------------------------------- |
| Testes dinâmicos                          | 33 executados                                       |
| Testes existentes de segurança/middleware | 83 passed                                           |
| Suíte completa                            | 587 passed em 12,84 s                               |
| Validador arquitetural                    | `correct` (17 verificações, 29 regras, 0 violações) |
| Código de produção alterado               | **não**                                             |
| Segredos reais nos artefatos              | **não**; valores redigidos                          |
| Cenários destrutivos                      | nenhum                                              |
| Dados sintéticos                          | sim; SQLite temporário                              |
| Resultado bruto × registro de achados     | consistente                                         |

### Comandos de reprodução

```powershell
py observatory/audits/etapa_5/run_security_tests.py
py -m pytest -q tests/security tests/middleware
py -m pytest -q
```

### Conclusão

A Etapa 5 foi concluída **na extensão dos testes realizados**. Não foi encontrada uma vulnerabilidade de segurança confirmada nos cenários examinados. Foram confirmados controles importantes — headers, validação de presença, hash bcrypt, proteção contra mass assignment e consultas parametrizadas — e foram identificados riscos condicionais relevantes: endpoint público de escrita, ausência de autenticação/autorização, validação de tipo/tamanho insuficiente, controles de proteção inativos, configuração de desenvolvimento exposta e lacuna de auditoria sob concorrência. A ausência de achados não deve ser lida como “aplicação segura”; ela reflete o escopo e as limitações acima.
