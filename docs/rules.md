# Regras arquiteturais da SOLAR

O catálogo das regras: **o que cada uma barra** e **o que ela libera**.

| Número | Situação                                                                               |
| ------ | -------------------------------------------------------------------------------------- |
| **31** | códigos na numeração (`001`–`030` e `032`)                                             |
| **30** | classes de regra implementadas — a **004** foi absorvida pela 001 e não tem classe     |
| **29** | regras aplicadas pelo `check`, em **17 verificações**                                  |
| **1**  | sem verificação estática: a **015** (contrato nomeado do UseCase), que não tem scanner |

---

| Código                 | Regra                                                                                         | Fluxo / restrição                                                                                                                                                                                                                                                                                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SOLAR-ARCH-001**     | **Planet não pode depender diretamente de outro Planet**                                      | `Planet → Planet` [X]                                                                                                                                                                                                                                                                                                                                   |
| **SOLAR-ARCH-002**     | **Repository não pode depender diretamente de Database**                                      | `Repository → Database` [X]                                                                                                                                                                                                                                                                                                                             |
| **SOLAR-ARCH-003**     | **Repository deve utilizar Persistence para acesso a dados**                                  | `Repository → Persistence → Database` [OK]                                                                                                                                                                                                                                                                                                              |
| **SOLAR-ARCH-004**     | **Planets não se comunicam diretamente entre si**                                             | Comunicação entre módulos deve passar por **Satellites** _(implementada pela SOLAR-ARCH-001)_                                                                                                                                                                                                                                                           |
| **SOLAR-ARCH-005**     | **Models não devem conhecer Persistence**                                                     | `Model → Persistence` [X]                                                                                                                                                                                                                                                                                                                               |
| **SOLAR-ARCH-006**     | **Models acessam a infraestrutura ORM através do Database**                                   | `Model → Database → ORM` [OK]                                                                                                                                                                                                                                                                                                                           |
| **SOLAR-ARCH-007**     | **Persistence pertence à camada de Database de Orbits**                                       | `orbits.database.persistence`                                                                                                                                                                                                                                                                                                                           |
| **SOLAR-ARCH-008**     | **Database do Nucleus é a fachada da infraestrutura de persistência**                         | `Orbits → Nucleus.Database → Driver`                                                                                                                                                                                                                                                                                                                    |
| **SOLAR-ARCH-009**     | **Driver não deve ser conhecido pelos módulos de negócio**                                    | `Planet → DriverSQLAlchemy` [X]                                                                                                                                                                                                                                                                                                                         |
| **SOLAR-ARCH-010**     | **Driver é responsável pela implementação tecnológica da persistência**                       | `Database → DriverSQLAlchemy → SQLAlchemy`                                                                                                                                                                                                                                                                                                              |
| **SOLAR-ARCH-011**     | **Planets não devem conhecer detalhes da infraestrutura do Nucleus**                          | acesso somente através das abstrações/fachadas arquiteturais definidas                                                                                                                                                                                                                                                                                  |
| **SOLAR-ARCH-012**     | **Satellites são a fronteira de comunicação externa/intermódulo**                             | `Planet → Satellite → Planet/serviço externo`                                                                                                                                                                                                                                                                                                           |
| **SOLAR-ARCH-013**     | **Toda entrada HTTP que transporta dados externos deve passar por Sanitization e Validation** | `HTTP Input → Validator → Sanitizer → Planet` [OK]; a rota declara `sanitizer=` e `validator=`; **o tipo de conteúdo não precisa ser declarado** — o que obriga o pipeline é a entrada transportar dados, não o verbo nem o `content_type`                                                                                                              |
| **SOLAR-ARCH-014**     | **Todo Controller deve retornar resposta processada por um Resource**                         | `Controller → Resource → Response` [OK]                                                                                                                                                                                                                                                                                                                 |
| **SOLAR-ARCH-015**     | **Controllers e UseCases não podem usar estruturas anônimas como contratos de entrada/saída** | contratos nomeados (`Input`/`Output`/`Entity`/`Resource`, mesmo herdando de `dict`/`list`) [OK]; built-ins literais [X]; coleções no processamento interno [OK]                                                                                                                                                                                         |
| **SOLAR-ARCH-016**     | **Rotas devem ser declaradas explicitamente em módulos de rotas**                             | `@app.route`/`@router.get` [X]; `Blueprint` + `add_url_rule` [OK]                                                                                                                                                                                                                                                                                       |
| **SOLAR-ARCH-017**     | **Toda rota deve apontar para um Controller**                                                 | `Route → Controller` [OK]; `Route → UseCase/Repository/Entity/Service/lambda` [X]                                                                                                                                                                                                                                                                       |
| **SOLAR-ARCH-018**     | **Toda rota deve ser declarada em um módulo de rotas próprio**                                | `orbits/routes.py` + `planets/<planet>/routes.py` [OK]; rota em `service.py`/`repository.py`/`controller.py`/`usecases/` [X]                                                                                                                                                                                                                            |
| **SOLAR-ARCH-019**     | **Todo Planet deve possuir a estrutura padrão**                                               | `__init__.py` + `routes.py` (arquivos) e `atmosphere/` + `controllers/` + `entity/` + `repository/` + `resources/` + `usecases/` (diretórios) [OK]; `repository.py` solto [X] (deve ser diretório)                                                                                                                                                      |
| **SOLAR-ARCH-020**     | **Credenciais e segredos não podem estar hardcoded no código**                                | `SECRET_KEY = "abc"` [X]; `os.environ[...]` / `environment.get(...)` [OK]; valor com o prefixo `SOLAR_DEFAULT` [OK] (é default, espera o ambiente); trecho anotado com `# solar:allow-secret` [OK]                                                                                                                                                      |
| **SOLAR-ARCH-021**     | **Segredos não podem ser retornados por Resources**                                           | `Resource` expondo `password`/`password_hash`/`secret_key`/`database_password`/tokens [X]                                                                                                                                                                                                                                                               |
| **SOLAR-ARCH-022**     | **Controllers não devem implementar autenticação diretamente**                                | `Controller` usando `hashlib`/`bcrypt`/`jwt`/`secrets`/`hmac` [X]; componentes de `nucleus.security` [OK]                                                                                                                                                                                                                                               |
| **SOLAR-ARCH-023**     | **Secrets não podem estar no código-fonte**                                                   | detecção por **conteúdo** (chave AWS, `-----BEGIN PRIVATE KEY-----`, JWT, `ghp_…`) independente do nome [X]; `os.environ[...]` [OK]. **Ignorados:** diretórios sem código de produção (`tests/`, `fixtures/`, `examples/`), blocos de documentação, valores de exemplo/placeholder (`…EXAMPLE`, `…fake…`) e o marcador revisável `# solar:allow-secret` |
| **SOLAR-ARCH-024**     | **Persistência não pode construir SQL inseguro**                                              | `"… WHERE id = " + x` / f-string / `%` / `.format()` [X]; SQL estático parametrizado (`:id`) [OK]                                                                                                                                                                                                                                                       |
| **SOLAR-ARCH-025**     | **Upload seguro: arquivo deve passar pela abstração Storage**                                 | `Controller` com `open`/`write_bytes`/`shutil`/`mimetypes` [X]; delegar ao UseCase → `Storage.save(...)` [OK]                                                                                                                                                                                                                                           |
| **SOLAR-ARCH-026**     | **Autenticação não deve ficar espalhada pelos Controllers**                                   | `current_user`/`is_authenticated`/`has_permission`/`abort(401)` no Controller [X]; componente de `nucleus.security` + middleware [OK]                                                                                                                                                                                                                   |
| **SOLAR-ARCH-027**     | **JWT/Token seguro**                                                                          | `algorithm="none"`, algoritmo implícito, `verify_signature: False` ou token sem `exp` [X]; algoritmo explícito + `exp` + verificação [OK]                                                                                                                                                                                                               |
| **SOLAR-ARCH-028**     | **Erros não podem vazar informações internas**                                                | `return {"error": str(e)}` / `f"{e}"` / `e.args` / `traceback.format_exc()` na resposta [X]; detalhe só no log → `ErrorHandler().handle(e)` [OK]                                                                                                                                                                                                        |
| **SOLAR-ARCH-029**     | **Dados da requisição não podem virar Entity/Model diretamente (mass assignment)**            | `DocumentEntity(**request.json)` / `from_dict(request.json)` / `update(**payload)` / `setattr` em laço [X]; campos explícitos ou `**DocumentInput(...)` [OK]                                                                                                                                                                                            |
| **SOLAR-ARCH-030**     | **Chamadas externas não podem usar URL não confiável (SSRF)**                                 | `requests.get(request.args["url"])` / `f"http://{host}/…"` / `get(url)` [X]; constante `BASE_URL`, `environment.get(…)` [OK]; dinâmica → `UrlGuard` [OK]                                                                                                                                                                                                |
| ~~**SOLAR-ARCH-031**~~ | ~~Rotas que mudam estado devem declarar proteção CSRF~~                                       | **Regra removida** — o CSRF passou a ser responsabilidade do pipeline (`SecurityPolicy`), não de cada rota                                                                                                                                                                                                                                              |
| **SOLAR-ARCH-032**     | **Cada Model deve ficar no seu próprio arquivo**                                              | `entities.py` com `class UserModel` **e** `class DocumentModel` [X]; `user_model.py` com um Model [OK]. Model reconhecido por `models` no caminho, por módulo `*_model` ou por classe `*Model`                                                                                                                                                          |

---

## Como verificar

```bash
python observatory/solar check              # verifica o diretório atual
python observatory/solar check <caminho>    # verifica outro projeto
```

O comando roda **todas** as regras que têm scanner estático e mostra o
status de **cada** verificação:

```text
SOLAR — verificação arquitetural

Dependency                violation
HttpInput                 correct
RouteDeclaration          correct
PlanetStructure           violation
SecretLiteral             violation
...

resultado: violation — 8 violação(ões) em 3 regra(s)
auditoria: observatory/solar/check/check-2026-10-05-143000.md
```

Quando há violação, o detalhe de cada regra aparece logo abaixo da lista.

| `resultado` | Código de saída | Significado                              |
| ----------- | --------------- | ---------------------------------------- |
| `correct`   | `0`             | nenhuma violação                         |
| `violation` | `1`             | houve violação                           |
| —           | `2`             | caminho inválido ou comando desconhecido |

O código de saída é o ponto do comando: é ele que faz a esteira de
integração contínua **reprovar** o build.

```bash
python observatory/solar check || exit 1     # esteira de integração contínua
```

### Auditoria

**Toda** verificação é registrada em Markdown dentro de
`observatory/solar/check/` — momento da execução (hora de **São Paulo**), raiz
verificada, status de todas as verificações e o detalhe de cada violação.

O nome carrega o momento e o resultado
(`check-2026-10-05-155458-violation.md`), então o arquivo mais recente diz,
sem precisar abrir, se a última verificação passou. Ver `observatory/README.md`.

### Escopo

Os **testes não são verificados**.

Um teste precisa justamente quebrar as regras para validar comportamento e
descobrir falhas — importar a ORM direto, montar um SQL na mão, declarar um
Model na hora. Cobrar arquitetura de teste é cobrar do lugar errado, e o
resultado é a regra ficar vermelha por causa de um `assert`.

Ficam de fora, em qualquer nível:

| Categoria | O que sai                                                                                                                                 |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Testes    | `tests/`, `test/`, `spec/`, `specs/`, `fixtures/`                                                                                         |
| Apoio     | `examples/`, `samples/`                                                                                                                   |
| Nome      | `conftest.py`, `test_*.py`, `*_test.py` (onde quer que estejam)                                                                           |
| Técnicos  | `.git/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.tox/`, `.venv/`, `venv/`, `__pycache__/`, `build/`, `dist/`, `node_modules/` |

A exclusão é por **diretório**, não por nome parecido: um `tests.py` continua
sendo analisado — é um arquivo como outro qualquer.

A exclusão acontece no **scanner**, não na Rule: o arquivo de teste nem chega a
ser interpretado. Ver `nucleus/rules/scanner/source_files.py`.

### Cobertura

| Situação                 | Regras                                                       |
| ------------------------ | ------------------------------------------------------------ |
| Verificadas pelo comando | as **29** com scanner estático, em 17 verificações           |
| Sem verificação          | **015** — o contrato nomeado do UseCase não tem scanner      |
| Absorvida                | **004** — virou a SOLAR-ARCH-001                             |
| Removida                 | **031** — o CSRF passou a ser do pipeline (`SecurityPolicy`) |

### Documentação

- **`docs/manual.md`** — manual completo: conceitos, cada classe e método do Nucleus, casos de
  uso, as **30** regras com violação e correção, e como estender a arquitetura.
- **`docs/manual.pdf`** — o mesmo manual em PDF.
- **`observatory/records/`** — o registro de erros do Observatório, em banco SQLite próprio.

Editou o Markdown? Regenere o PDF:

```powershell
.\docs\build\build-pdf.ps1
```

**004** e **015** não aparecem no relatório: a 004 foi absorvida pela 001, e a 015
(o contrato nomeado do UseCase) ainda não tem scanner.
