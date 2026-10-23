# Inventário de controles de segurança

**Data:** 2026-10-23  
**Método:** inspeção estática do código e confirmação dos pontos de instanciação; os testes dinâmicos estão em [`RESULTADOS_TESTES.json`](../dados/RESULTADOS_TESTES.json) e no [`RELATORIO_ETAPA_5.md`](RELATORIO_ETAPA_5_EXECUCAO.md).

> **Regra:** a existência de uma classe não significa que o controle esteja ativo. A coluna **Ativo?** indica se ele é instanciado no caminho real da aplicação.

---

## 1. Controles ativos

| Controle                                              | Definição                                                | Onde é definido                                                                                                      | Onde é instanciado                                                                  | Ponto de execução                       | Ativo?                             | Evidência                                                                          |
| ----------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------- |
| `RequestPipeline` + `JsonValidator` + `JsonSanitizer` | valida presença de campos e normaliza o corpo JSON       | `nucleus/middleware/request_pipeline.py`; `nucleus/security/json_validator.py`; `nucleus/security/json_sanitizer.py` | `Kernel.mount` (`self.request_pipeline`); `SolarBlueprint`/`Atmosphere` para a rota | `before_request` do Blueprint do Planet | **sim**, no `POST /examples/users` | `orbits/planets/example/routes.py` declara `sanitizer=`/`validator=`; testes D1–D8 |
| `SecurityHeaders`                                     | aplica `nosniff`, `DENY` e `no-referrer`                 | `nucleus/middleware/security_headers.py`                                                                             | `Kernel.mount` (`headers = SecurityHeaders(self.security)`)                         | `after_request` global                  | **sim**, em todas as respostas     | testes A1, A2, A4, B1, D1, D9                                                      |
| `ErrorHandler`                                        | resposta genérica com código, mensagem fixa e referência | `nucleus/middleware/error_handler.py`                                                                                | `Kernel.mount` (`self.error_handler`)                                               | `@app.errorhandler(Exception)`          | **sim**                            | respostas 400/500 sem detalhe interno; testes D1–D10                               |
| `Password` (bcrypt)                                   | gera hash de senha                                       | `nucleus/security/password.py`                                                                                       | `UserEntity.__init__`                                                               | criação de usuário                      | **sim**                            | B1: hash bcrypt no banco; senha em texto não retorna                               |
| `Identity`                                            | garante `SECRET_KEY` e `SOLAR_ID`                        | `nucleus/security/identity.py`                                                                                       | `Kernel.mount`                                                                      | montagem                                | **sim**                            | chave usada como `app.secret_key`; `.env` temporário no teste                      |
| `Database` / `DriverSQLAlchemy`                       | acesso à persistência                                    | `nucleus/database/database.py`; `driver_sqlalchemy.py`                                                               | `Kernel.mount`                                                                      | criação/consulta                        | **sim**                            | teste de criação e consulta direta ao SQLite                                       |

### 1.1 O que cada controle ativo cobre

- **Entrada JSON:** cobre presença, `None`, texto em branco, `strip()` e descarte de chaves nulas. **Não** cobre tipo, tamanho máximo, faixa de valores ou regra de senha.
- **Headers:** cobre os três obrigatórios em qualquer resposta. **Não** configura CSP, HSTS ou CORS.
- **Erros:** cobre exceções não tratadas e evita vazamento de detalhe. **Não** preserva corretamente o status de `HTTPException` (404/405 viram 500 — ver achado).
- **Senha:** usa bcrypt com salt; **não** há política de comprimento/complexidade.

---

## 2. Controles existentes, mas inativos

| Controle                                   | Definido em                               | Instanciado no caminho? | Situação                                                                                                    | Evidência                                                                                                               |
| ------------------------------------------ | ----------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `CsrfProtection`                           | `nucleus/middleware/csrf_protection.py`   | **não**                 | `SecurityPolicy.csrf_enabled=True` é apenas um campo; o `Kernel` não cria `CsrfProtection` nem valida token | busca por `CsrfProtection(` não encontra uso em `nucleus/`, `orbits/`, `server.py`; POST B1 funciona sem `X-CSRF-Token` |
| `RateLimiter`                              | `nucleus/middleware/rate_limiter.py`      | **não**                 | opcional (`rate_limit_enabled=False`), sem middleware que responda 429                                      | 10 tentativas inválidas (F1–F10) retornaram 400, nenhuma 429                                                            |
| `BruteForceGuard`                          | `nucleus/middleware/brute_force_guard.py` | **não**                 | não há fluxo de login; guard não é chamado                                                                  | não há rota de login; busca por instanciação vazia                                                                      |
| `UrlGuard`                                 | `nucleus/security/url_guard.py`           | **não**                 | não há chamada externa no código atual; guarda não é usada                                                  | não há `Satellites` nem cliente HTTP de produção                                                                        |
| `Token` (JWT)                              | `nucleus/security/token.py`               | **não**                 | não há autenticação; `PyJWT` não está instalado                                                             | `import nucleus.security.token` → `ModuleNotFoundError: jwt`; apenas teste de scanner importa a classe                  |
| `FileValidator` / `FileSanitizer` / upload | `nucleus/upload/*`                        | **não**                 | não há rota de upload                                                                                       | rotas existentes: somente health e criação de usuário                                                                   |
| `AttemptTracker`                           | `nucleus/security/attempt_tracker.py`     | **não**                 | estado auxiliar de rate/brute force, que não estão ativos                                                   | sem instanciação de produção                                                                                            |

**Consequência:** CSRF, rate limiting, brute force, JWT e upload **não protegem** os caminhos HTTP atuais. Isso não significa, por si, que sejam vulnerabilidades: depende do desenho e da exposição do endpoint.

---

## 3. Categorias sem mecanismo correspondente

| Categoria                                | Situação                             | Justificativa                                                                                                                    |
| ---------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Autenticação                             | **não implementada no caminho HTTP** | não há login, sessão autenticada, middleware de autenticação nem validação de `Authorization`; C1/C2 retornam 201 sem credencial |
| Autorização / papéis                     | **não implementada**                 | não há perfis, permissões, proprietário de recurso nem checagem de acesso                                                        |
| IDOR / acesso a recurso de outro usuário | **não aplicável ao conjunto atual**  | não existe rota de leitura/atualização por identificador; `GET /examples/users/1` não é rota                                     |
| Comunicação entre serviços / Satellites  | **não aplicável**                    | não há pasta/módulo de satélites nem chamada externa no código atual                                                             |
| Upload de arquivos                       | **não aplicável**                    | módulos existem, mas nenhuma rota os utiliza                                                                                     |
| Banco com permissões por usuário         | **não aplicável**                    | a aplicação usa uma credencial de banco única; não há usuário de banco por identidade de aplicação                               |

---

## 4. Configuração e exposição

| Item                  | Observação                                                                                                                     | Classificação inicial                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| `.env`                | ignorado pelo Git (`.gitignore`); contém configuração de DEV, incluindo credenciais de banco de desenvolvimento e `SECRET_KEY` | configuração suspeita se o arquivo for exposto fora do ambiente local             |
| `docker-compose.yml`  | `APP_ENV=DEV`, `DEV_HOST=0.0.0.0`, porta `5000:5000`, PostgreSQL com `postgres/postgres`                                       | configuração suspeita para uso fora de desenvolvimento; o banco não publica porta |
| `server.py`           | `debug=config.get("APP_ENV") == "DEV"`                                                                                         | configuração suspeita se DEV for exposto; no teste `TEST`, debug desligado        |
| CORS                  | `Environment` lê `CORS_ORIGINS`, mas nenhum middleware aplica CORS                                                             | configuração não utilizada; ausência de `Access-Control-Allow-Origin` observada   |
| CSP/HSTS              | `SecurityPolicy` permite, mas os valores padrão são `None`                                                                     | headers opcionais ausentes por padrão                                             |
| `Server` header       | Werkzeug envia `Server: Werkzeug/3.1.9 Python/3.14.7`                                                                          | informação de versão exposta no servidor de teste; baixo impacto                  |
| Banco do Observatório | SQLite local, sem rota de leitura                                                                                              | não exposto pela API; registra detalhe interno                                    |

---

## 5. Superfície de ataque observada

| Superfície              | Exposição                    | Controles                                                                                                  |
| ----------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `GET /solar/health`     | pública, sem dados           | headers; sem autenticação (esperado para health)                                                           |
| `POST /examples/users`  | pública, cria usuário        | validação/sanitização JSON, bcrypt, ORM parametrizada; **sem autenticação, autorização, CSRF, rate limit** |
| `GET /qualquer-rota`    | 404                          | `ErrorHandler` genérico, mas status vira 500                                                               |
| `OPTIONS /solar/health` | resposta automática do Flask | sem CORS; `Allow` presente                                                                                 |
| Banco SQLite local      | arquivo no `tmp/` do teste   | sem exposição de rede; sem criptografia em repouso (SQLite padrão)                                         |

---

## 6. Resumo do inventário

- **Ativos:** validação/sanitização JSON, headers obrigatórios, tratamento genérico de erros, bcrypt, identidade e persistência.
- **Inativos:** CSRF, rate limit, brute force, URL guard, JWT, upload.
- **Ausentes:** autenticação, autorização, papéis, isolamento por processo/permissões, satélites.
- **Configuração a revisar:** CORS não aplicado, debug em DEV, Docker em `0.0.0.0`, credenciais de desenvolvimento, ausência de limites de corpo/tamanho.
