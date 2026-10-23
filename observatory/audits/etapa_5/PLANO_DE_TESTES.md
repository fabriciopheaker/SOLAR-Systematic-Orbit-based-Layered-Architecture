# Plano de testes — Etapa 5: segurança e isolamento

**Projeto:** SOLAR  
**Data:** 2026-10-23  
**Ambiente:** Windows 11, Python 3.14.7, aplicação local em `127.0.0.1`  
**Artefatos:** `observatory/audits/etapa_5/`

---

## 1. Perguntas

1. Quais controles de segurança existem no código?
2. Quais estão realmente ativos no caminho HTTP?
3. O que pode ser validado dinamicamente com dados sintéticos?
4. Há exposição de segredos, dados internos ou mensagens detalhadas?
5. Há falhas de validação, autorização ou isolamento demonstráveis?
6. Quais categorias não podem ser testadas por falta de mecanismo ou ambiente?

## 2. Escopo real

| Item                     | Constatação inicial                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------- |
| Rotas                    | `GET /solar/health`; `POST /examples/users`                                         |
| Autenticação             | não há rota de login nem middleware de autenticação no caminho HTTP                 |
| Autorização              | não há papéis, permissões ou checagem por proprietário                              |
| Entrada                  | `JsonValidator` + `JsonSanitizer` no `POST /examples/users`                         |
| Senhas                   | bcrypt em `nucleus/security/password.py`                                            |
| Headers                  | `SecurityHeaders` aplicado em `after_request`                                       |
| Erros                    | `ErrorHandler` genérico + Observatório                                              |
| CSRF                     | classe existe; `SecurityPolicy.csrf_enabled=True`; não há instanciação no `Kernel`  |
| Rate limit / brute force | classes existem; opcionais e não instanciadas                                       |
| URL guard                | classe existe; não usada por não haver chamada externa                              |
| Token JWT                | classe existe; `PyJWT` não está instalado; não é usada pela aplicação               |
| Upload                   | módulos existem; não há rota de upload                                              |
| Satellites               | não há pasta/módulo de satélites no código atual                                    |
| Banco                    | SQLite temporário no teste; PostgreSQL não disponível isoladamente                  |
| Segredos                 | `.env` ignorado pelo Git; `docker-compose.yml` contém credencial de desenvolvimento |

## 3. Hipóteses

| ID  | Hipótese                                                                | Verificação                                    |
| --- | ----------------------------------------------------------------------- | ---------------------------------------------- |
| H1  | Os três headers obrigatórios são aplicados em respostas 200/201/400/500 | inspeção HTTP                                  |
| H2  | O `POST` valida presença, mas não tipos nem limites de tamanho          | payloads vazios, nulos, tipos errados e 64 KiB |
| H3  | O endpoint de criação é público e não exige CSRF                        | requisições sem credencial e sem token CSRF    |
| H4  | Não há autorização por proprietário porque não há rota de leitura       | tentativa de `GET` por identificador           |
| H5  | Consultas ORM são parametrizadas; injeção SQL no nome não executa       | nome com payload SQL e consulta posterior      |
| H6  | Segredos de resposta e detalhes internos não vazam                      | respostas 400/500 e inspeção de campos         |
| H7  | CSRF, rate limit, brute force e JWT existem apenas como código/teste    | busca de instanciação e teste de importação    |

## 4. Cenários

| Teste | Categoria                | Cenário                                                                                                                | Dados                        |
| ----- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| A     | Configuração             | health, 404, OPTIONS/CORS, método não permitido                                                                        | nenhum                       |
| B     | Referência               | criação válida, headers e corpo                                                                                        | e-mail sintético único       |
| C     | Autenticação/autorização | POST sem credencial; Bearer inválido; GET por ID                                                                       | e-mails sintéticos           |
| D     | Validação                | corpo vazio, branco, nulo, e-mail inválido, duplicado, JSON malformado/lista, tipo errado, senha curta, nome de 64 KiB | sintéticos                   |
| E     | Entrada/isolamento       | campos extras/protegidos, payload SQL no nome, script HTML no nome                                                     | sintéticos                   |
| F     | Proteção                 | 10 tentativas inválidas repetidas; observar 429/bloqueio                                                               | e-mails inválidos            |
| G     | Banco/resposta           | verificar hash, normalização, campos protegidos e tabela após payload SQL                                              | leitura do SQLite temporário |

## 5. Limites de segurança

- Somente `127.0.0.1`; porta efêmera.
- Sem carga, sem concorrência, sem testes destrutivos.
- Sem exclusão de dados; banco criado do zero em `tmp/`.
- Sem credenciais reais; todos os e-mails e senhas são sintéticos.
- Sem tentativas de contornar autenticação ou explorar serviços externos.
- Sem instalação de dependências.
- Sem alteração de código de produção.
- Se um teste puder causar instabilidade, ele não será executado.

## 6. Critérios de classificação

- **Vulnerabilidade confirmada:** violação reproduzível de um controle.
- **Risco potencial:** indício técnico sem exploração demonstrada.
- **Configuração suspeita:** configuração que merece revisão.
- **Controle validado no cenário testado:** comportamento esperado observado.
- **Inconclusivo:** dados insuficientes.
- **Não aplicável:** categoria sem mecanismo correspondente.
- **Bloqueado:** dependência ou ambiente ausente.
- **Não executado:** fora do escopo ou interrompido.

Severidade será qualitativa (**baixa/média/alta**) e sempre acompanhada do critério: impacto + facilidade de exploração + evidência. Não será usada uma pontuação CVSS sem cálculo formal.

## 7. Reprodutibilidade

```powershell
py observatory/audits/etapa_5/run_security_tests.py
```

O script inicia `security_server.py` em processo separado, com SQLite e `.env` temporários, executa os testes, grava `RESULTADOS_TESTES.json` e encerra o servidor.
