# Relatório técnico — Etapa 5: segurança e isolamento

**Projeto:** SOLAR
**Data:** 2026-10-23
**Ambiente:** Windows 11, Python 3.14.7, Flask 3.1.3, SQLite temporário,
`127.0.0.1`
**Testes:** 33 HTTP, dados sintéticos, sem carga e sem ações destrutivas
**Código de produção alterado:** não

---

## 1. Objetivo e escopo

A etapa responde:

1. Quais controles de segurança existem no código?
2. Quais estão efetivamente ativos no caminho HTTP?
3. Quais riscos são observáveis no estado atual?
4. O que não é testável com o conjunto atual de rotas?

O escopo inclui `nucleus/kernel.py`, `nucleus/security/`,
`nucleus/middleware/`, `nucleus/upload/`, `orbits/planets/example/`,
`orbits/planets/solar/`, `orbits/database/`, `server.py`, `.env` e
`docker/docker-compose.yml`.

**Não inclui:** teste de penetração, scanner SAST/DAST, análise de dependências
(CVE), revisão criptográfica ou teste de infraestrutura real.

---

## 2. Método

1. Inspeção estática de rotas, imports, instanciação e configuração.
2. Verificação dos testes existentes.
3. Execução do servidor em processo separado, com SQLite, `.env` e storage
   temporários.
4. Testes HTTP com dados sintéticos.
5. Leitura direta do SQLite temporário para confirmar hash, campos e
   integridade.
6. Classificação qualitativa dos achados, sem CVSS formal.

**Ferramentas externas:** nenhuma. Não foram usados Sonar, Bandit, OWASP ZAP,
Burp ou scanner de segredos. A ausência de scanner é uma limitação declarada.

---

## 3. Categorias avaliadas

| Categoria        | O que foi feito                                         | Resultado                                   |
| ---------------- | ------------------------------------------------------- | ------------------------------------------- |
| A — Autenticação | POST sem credencial e com Bearer inválido               | não implementada; endpoint público          |
| B — Autorização  | busca por papéis/permissões; acesso por ID              | não implementada; sem rota por ID           |
| C — Isolamento   | imports, estado global, `Database`, limites de processo | mesmo processo; sem isolamento real         |
| D — Entrada      | corpo vazio, inválido, tipos, 64 KiB                    | presença/JSON validados; tipo/tamanho não   |
| E — Segredos     | `.env`, compose, respostas, erros, banco                | sem segredo real versionado; credencial DEV |
| F — Comunicação  | Satellites, clientes HTTP                               | não aplicável no código atual               |
| G — Configuração | headers, CORS, debug, host/porta, banco                 | 3 headers; CSP/HSTS/CORS ausentes           |
| H — Proteção     | onde cada mecanismo é definido/instanciado              | 5 ativos; 5 inativos                        |

---

## 4. Resultados dos testes

### 4.1 Distribuição por status

| Status    | Quantidade | Observação                                                   |
| --------- | ---------- | ------------------------------------------------------------ |
| 200       | 2          | health e OPTIONS                                             |
| 201       | 8          | criações válidas/extras/SQL/XSS/senha curta/64 KiB           |
| 400       | 18         | validações, duplicidade, JSON inválido, tentativas inválidas |
| 500       | 5          | 2 tipos errados + 3 `HTTPException` mascaradas               |
| **Total** | **33**     |                                                              |

### 4.2 Casos principais

| ID     | Teste                              | Resultado                         | Interpretação                       |
| ------ | ---------------------------------- | --------------------------------- | ----------------------------------- |
| A1     | health                             | 200, JSON, 3 headers              | rota pública e funcional            |
| A2     | rota inexistente                   | **500**, code=404                 | erro de cliente mascarado           |
| A3     | OPTIONS com Origin                 | 200, sem ACAO                     | CORS não habilitado                 |
| A4     | método não permitido               | **500**, code=405                 | erro de cliente mascarado           |
| B1     | criação válida                     | 201; banco com `$2...`            | bcrypt; resposta segura             |
| C1     | POST sem credencial                | 201                               | endpoint público                    |
| C2     | POST com Bearer inválido           | 201                               | credencial ignorada                 |
| C3     | GET por ID                         | **500**, code=404                 | rota inexistente; sem IDOR testável |
| D1–D3  | vazio/branco/nulo                  | 400 `MISSING_FIELDS`              | validação de presença               |
| D4     | e-mail inválido                    | 400 `INVALID_EMAIL`               | regra de domínio                    |
| D5     | e-mail duplicado                   | 400 `EMAIL_TAKEN`                 | consulta e regra                    |
| D6–D8  | JSON malformado/lista/content-type | 400 `INVALID_JSON_BODY`           | guarda de entrada                   |
| D9     | `senha=123`                        | **500** `INTERNAL_ERROR`          | tipo não validado                   |
| D10    | `email=123`                        | **500** `INTERNAL_ERROR`          | tipo não validado                   |
| D11    | senha `"x"`                        | 201                               | sem política de senha               |
| D12    | nome de 64 KiB                     | 201                               | sem limite de tamanho               |
| E1     | campos extras/protegidos           | 201; id 6; reset=false            | sem mass assignment                 |
| E2     | payload SQL no nome                | 201; nome literal; tabela intacta | ORM parametrizada                   |
| E3     | `<script>` no nome                 | 201; texto literal em JSON        | depende do consumidor               |
| F1–F10 | 10 tentativas inválidas            | 400, sem 429                      | sem rate limit                      |

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

| ID            | Status                | Severidade | Achado                                       |
| ------------- | --------------------- | ---------- | -------------------------------------------- |
| SEC-AUTH-01   | risco potencial       | média      | criação de usuário pública, sem autenticação |
| SEC-AUTH-02   | risco potencial       | baixa      | senha de 1 caractere aceita                  |
| SEC-AUTHZ-01  | não aplicável         | —          | sem autorização/IDOR no conjunto atual       |
| SEC-INPUT-01  | risco potencial       | baixa      | tipo numérico causa 500                      |
| SEC-INPUT-02  | risco potencial       | média      | sem limite de corpo/campo                    |
| SEC-PROT-01   | configuração suspeita | baixa      | CSRF inativo                                 |
| SEC-PROT-02   | configuração suspeita | baixa      | rate limit/brute force inativos              |
| SEC-ERROR-01  | configuração suspeita | baixa      | 404/405 viram 500                            |
| SEC-CONFIG-01 | configuração suspeita | média      | debug/`0.0.0.0`/credencial DEV               |
| SEC-CONFIG-02 | configuração suspeita | baixa      | CSP/HSTS/CORS não aplicados                  |
| SEC-CONFIG-03 | configuração suspeita | baixa      | header `Server` expõe versões                |
| SEC-SECRET-01 | configuração suspeita | baixa      | credencial padrão de desenvolvimento         |
| SEC-JWT-01    | bloqueado             | —          | módulo JWT sem dependência e inativo         |
| SEC-LOG-01    | risco potencial       | média      | falha de log do Observatory sob concorrência |
| SEC-XSS-01    | inconclusivo          | —          | script armazenado; depende do consumidor     |
| SEC-SQLI-01   | controle validado     | —          | ORM parametrizada                            |
| SEC-MASS-01   | controle validado     | —          | campos extras ignorados                      |

### 5.1 Critério de severidade

- **baixa:** impacto limitado a robustez, informação de versão ou configuração
  sem exposição demonstrada;
- **média:** impacto potencial em disponibilidade, integridade ou abuso de
  endpoint público, com exploração plausível;
- **alta:** não atribuída nesta auditoria;
- **não aplicável/bloqueado:** não há mecanismo ou dependência para testar.

Não foi aplicada pontuação CVSS formal. A severidade é uma estimativa
condicionada ao ambiente local e às limitações declaradas.

---

## 6. Isolamento

| Aspecto       | Observação                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------------- |
| Processo      | servidor e cliente em processos separados no teste, mas a aplicação é um único processo Python |
| Estado global | `Database`, `Storage`, `Broadcast` e `UserPersistency` são singletons/classes de estado        |
| Sessão        | uma `Session` SQLAlchemy compartilhada (ver etapa 4)                                           |
| Permissões    | não há separação de permissões por rota                                                        |
| Rede          | bind local no teste; configuração de desenvolvimento permite `0.0.0.0`                         |
| Dados         | SQLite temporário; sem segredo real                                                            |

**Conclusão:** não há isolamento real de processo, permissões ou sessão. O termo
“isolamento” nesta etapa significa que a execução foi separada do ambiente de
desenvolvimento, não que a aplicação isole tenants ou privilégios.

---

## 7. Observabilidade

`ErrorLog` cria a conexão SQLite na thread principal e a usa em threads de
requisição. Em concorrência, ocorre `sqlite3.ProgrammingError`; o
`ErrorHandler` silencia a falha do observador. Resultado: **0 erros registrados**
no log durante os testes, apesar de respostas 500.

Esse é um risco de observabilidade, não de segurança de entrada. Foi
classificado como `SEC-LOG-01` (média) porque afeta a capacidade de detectar e
investigar incidentes.

---

## 8. Limitações

1. **Sem scanner externo:** não houve SAST/DAST, análise de dependências ou
   teste de penetração.
2. **Sem autenticação implementada:** não é possível testar IDOR, escalada de
   privilégio ou bypass de autorização.
3. **Sem rota de upload:** o subsistema de upload não foi exercitado via HTTP.
4. **Sem JWT instalado:** o módulo existe, mas não há dependência para testar.
5. **Ambiente local:** `127.0.0.1`, SQLite, sem proxy reverso, TLS ou WAF.
6. **Dados sintéticos:** não há dados reais, nem teste de privacidade.
7. **Amostra pequena:** 33 testes não cobrem toda a superfície.

---

## 9. Recomendações condicionadas

| Achado                     | Ação sugerida                                         | Não fazer                             |
| -------------------------- | ----------------------------------------------------- | ------------------------------------- |
| Endpoint público           | exigir autenticação/autorização se a rota for exposta | assumir que é público por desenho     |
| Sem tipo/tamanho           | validar tipos e limitar corpo/campos                  | confundir com “validação de presença” |
| 404/405 → 500              | corrigir o handler para preservar o status            | tratar como falha de negócio          |
| CSRF/rate/brute inativos   | ativar no pipeline se o cenário exigir                | ligar sem testar impacto              |
| Log falha sob concorrência | criar conexão por thread/uso                          | silenciar a falha                     |
| Debug/`0.0.0.0`            | restringir ao ambiente local                          | expor em produção                     |

---

## 10. Reprodução

```powershell
py observatory/audits/etapa_5_seguranca_isolamento/scripts/run_security_tests.py
```

Artefatos:

- `dados/RESULTADOS_TESTES.json`
- `dados/REGISTRO_ACHADOS.json`
- `dados/startup.json`
- `dados/tmp/security.sqlite`

---

## 11. Veredito da etapa

| Afirmação                             | Veredito                                 |
| ------------------------------------- | ---------------------------------------- |
| Os headers obrigatórios são aplicados | **sustentada**                           |
| O bcrypt é usado e a senha não vaza   | **sustentada**                           |
| O endpoint de criação é público       | **sustentada**                           |
| Não há validação de tipo/tamanho      | **sustentada**                           |
| CSRF/rate/brute estão inativos        | **sustentada**                           |
| Há SQL injection                      | **não sustentada**                       |
| A aplicação está isolada              | **não sustentada**                       |
| Há vulnerabilidade confirmada         | **não sustentada** nos cenários testados |
