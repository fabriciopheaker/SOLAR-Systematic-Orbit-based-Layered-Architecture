# Relatório técnico — Etapa 1: conformidade arquitetural

**Projeto:** SOLAR
**Data da execução:** 2026-10-23
**Ambiente:** Windows 11, Python 3.14.7
**Comando:** `py observatory/solar check`
**Evidência:** [`evidencias/check/check-2026-10-23-124423-correct.md`](evidencias/check/check-2026-10-23-124423-correct.md)
**Código de produção alterado nesta etapa:** não

---

## 1. Objetivo e escopo

Esta etapa responde a uma pergunta limitada: **o código atual satisfaz as regras
arquiteturais que o próprio projeto declara e consegue verificar
automaticamente?**

O objeto é o código de produção (`nucleus/`, `orbits/`, `observatory/` e
`server.py`), excluindo testes, exemplos e diretórios técnicos, conforme o
scanner de arquivos-fonte.

Não é objetivo desta etapa:

- provar que a arquitetura é “boa”;
- provar que as regras cobrem todos os riscos;
- medir desempenho, segurança em runtime ou manutenibilidade.

---

## 2. Método

1. Executar o comando oficial de verificação sobre a raiz do projeto.
2. Registrar o relatório Markdown gerado pelo próprio comando.
3. Conferir a quantidade de verificações e de regras no relatório.
4. Comparar o catálogo documentado (`docs/rules.md`) com o registro efetivo
   (`nucleus/rules/project_validator.py`).
5. Investigar as regras que não aparecem no relatório, em especial a ROF-003.
6. Verificar, no código e nos testes, se a regra ausente tem outra forma de
   execução.

---

## 3. Resultado da execução

| Item             | Resultado |
| ---------------- | --------- |
| Resultado global | `correct` |
| Verificações     | 17        |
| Regras aplicadas | 29        |
| Violações        | 0         |
| Regras violadas  | 0         |
| Código de saída  | 0         |

As 17 verificações são: `Dependency`, `HttpInput`, `RouteDeclaration`,
`PlanetStructure`, `SecretLiteral`, `ResourceExposure`,
`ControllerSecurityUsage`, `ControllerReturn`, `SecretOccurrence`,
`UnsafeSql`, `UploadHandling`, `ControllerAuthChecks`, `TokenUsage`,
`ErrorExposure`, `EntityBinding`, `OutboundRequest` e `ModuleClasses`.

---

## 4. Cobertura do catálogo

O catálogo tem **30 códigos**. Desses:

- **29** são aplicados pelo `check`, em 17 verificações;
- **1** não tem scanner estático: `SOLAR-ROF-003`;
- **1** foi absorvida: `SOLAR-RED-004` virou a `SOLAR-RED-001`.

### 4.1 Regras de dependência e persistência

| Código  | Classe                                     | Verificação  | Executada?    |
| ------- | ------------------------------------------ | ------------ | ------------- |
| RED-001 | `PlanetCannotDependOnPlanet`               | `Dependency` | sim           |
| RED-002 | `RepositoryCannotDependOnDatabase`         | `Dependency` | sim           |
| RED-003 | `RepositoryMustUsePersistence`             | `Dependency` | sim           |
| RED-004 | absorvida pela RED-001                     | —            | não se aplica |
| RED-005 | `ModelsCannotDependOnPersistence`          | `Dependency` | sim           |
| RED-006 | `ModelsMustAccessOrmThroughDatabase`       | `Dependency` | sim           |
| RED-007 | `PersistenceBelongsToOrbitsDatabase`       | `Dependency` | sim           |
| RED-008 | `OrbitsMustUseDatabaseFacade`              | `Dependency` | sim           |
| RED-009 | `PlanetCannotDependOnDriver`               | `Dependency` | sim           |
| RED-010 | `OrmBelongsToDriver`                       | `Dependency` | sim           |
| RED-011 | `PlanetCannotKnowNucleusInfrastructure`    | `Dependency` | sim           |
| RED-012 | `ExternalCommunicationBelongsToSatellites` | `Dependency` | sim           |

### 4.2 Regras estruturais e de fluxo HTTP

| Código  | Classe                                                            | Verificação        | Executada?         |
| ------- | ----------------------------------------------------------------- | ------------------ | ------------------ |
| ROF-001 | `HttpInputMustPassThroughSanitizationAndValidation`               | `HttpInput`        | sim                |
| ROF-002 | `ControllerMustReturnResource`                                    | `ControllerReturn` | sim                |
| ROF-003 | `ControllerAndUseCaseMustUseNamedContracts`                       | —                  | **não no `check`** |
| ROF-004 | `RoutesMustBeDeclaredExplicitly` + `RoutesMustLiveInRouteModules` | `RouteDeclaration` | sim                |
| ROF-005 | `RoutesMustPointToController`                                     | `RouteDeclaration` | sim                |
| ROF-006 | `PlanetMustHaveStandardStructure`                                 | `PlanetStructure`  | sim                |
| ROF-007 | `ModelsMustLiveInTheirOwnFile`                                    | `ModuleClasses`    | sim                |

### 4.3 Regras de segurança e dados

| Código  | Classe                                          | Verificação               | Executada? |
| ------- | ----------------------------------------------- | ------------------------- | ---------- |
| SEG-001 | `SecretsMustNotBeHardcoded`                     | `SecretLiteral`           | sim        |
| SEG-002 | `ResourcesMustNotExposeSecrets`                 | `ResourceExposure`        | sim        |
| SEG-003 | `ControllerMustNotImplementAuthentication`      | `ControllerSecurityUsage` | sim        |
| SEG-004 | `SecretsMustNotAppearInSource`                  | `SecretOccurrence`        | sim        |
| SEG-005 | `UploadsMustUseStorage`                         | `UploadHandling`          | sim        |
| SEG-006 | `AuthenticationMustNotBeScatteredInControllers` | `ControllerAuthChecks`    | sim        |
| SEG-007 | `TokensMustBeSecure`                            | `TokenUsage`              | sim        |
| SEG-008 | `ErrorsMustNotLeakInternals`                    | `ErrorExposure`           | sim        |
| SEG-009 | `RequestDataMustNotBecomeEntitiesDirectly`      | `EntityBinding`           | sim        |
| SEG-010 | `OutboundRequestsMustNotUseUntrustedUrl`        | `OutboundRequest`         | sim        |
| SEG-011 | `PersistenceMustNotBuildUnsafeSql`              | `UnsafeSql`               | sim        |

---

## 5. A ROF-003: o que é e o que não é

### 5.1 O que a regra exige

A `SOLAR-ROF-003` exige que Controllers e UseCases usem **contratos nomeados**
de entrada e saída — por exemplo, `CreateUserInput` e `CreateUserOutput` — e
não `dict`, `list`, `tuple`, `set` ou `frozenset` literais como contrato.
Coleções anônimas no processamento interno são permitidas.

A implementação está em
`nucleus/rules/architecture/controller_and_usecase_must_use_named_contracts.py`.
A classe `ControllerAndUseCaseMustUseNamedContracts` tem o código
`SOLAR-ROF-003` e um teste unitário próprio.

### 5.2 O que o `check` faz

O `ProjectValidator` declara explicitamente, em `project_checks()`, que a
ROF-003 fica fora do registro porque o contexto dela é o contrato nomeado do
UseCase e **não há scanner para produzi-lo**. Isso é verificado no código, não
apenas na documentação:

- não há chamada à classe em `project_checks()`;
- não há `Check("...", ...)` com essa regra;
- o teste unitário existe, mas testa a Rule isoladamente.

### 5.3 A conclusão anterior e a correção

A conclusão anterior dizia “ROF-003 não é executada”. A frase é **verdadeira
para o `ProjectValidator`**, mas incompleta, porque:

- a Rule existe;
- há teste unitário;
- a regra é exercitada quando um `ResponsibilityContract` é validado.

O erro a corrigir não é “a ROF-003 é executada pelo `check`”. O erro é usar a
ausência de scanner para sugerir que a **organização de persistência** também
está fora de conformidade. Não está: a persistência é coberta por regras
distintas, todas executadas.

### 5.4 A organização de persistência observada

| Elemento              | Caminho                                                   | Papel                                |
| --------------------- | --------------------------------------------------------- | ------------------------------------ |
| Model                 | `orbits/database/models/user_model.py`                    | um Model no próprio arquivo          |
| Persistence           | `orbits/database/persistence/users/user_persistency.py`   | acesso ao Model de usuário           |
| Repository            | `orbits/planets/user/repository/user_repository.py`       | recebe `UserPersistency` por injeção |
| Repository de exemplo | `orbits/planets/example/repository/example_repository.py` | usa `UserPersistency`                |
| Database              | `nucleus/database/database.py`                            | fachada do ORM                       |

O caminho `Repository → Persistence → Database` é exatamente o que as regras
RED-002, RED-003, RED-005, RED-006, RED-007 e RED-008 verificam. O relatório
`Dependency correct` confirma que o código atual não viola essas regras.

**Conclusão correta:** a conformidade é **parcialmente demonstrável** porque a
ROF-003 não tem scanner estático. A persistência, isoladamente, está conforme
as regras executadas. “100% conforme” continua não sendo uma afirmação
sustentável, mas por um motivo diferente do que a frase anterior sugeria.

---

## 6. Limitações

1. **Cobertura, não eficácia:** o `check` mostra que o código satisfaz as regras
   implementadas; não mostra que as regras detectam todos os problemas.
2. **ROF-003 sem scanner:** a regra não varre o projeto inteiro; depende de um
   contrato ser submetido à Rule.
3. **Escopo do scanner:** testes, exemplos e diretórios técnicos ficam fora.
4. **Sem runtime:** a etapa não verifica comportamento sob requisição, carga ou
   falha.
5. **Regra absorvida:** a RED-004 não tem classe própria; sua intenção está na
   RED-001.

---

## 7. Reprodução

```powershell
py observatory/solar check
```

O relatório é gravado em:

```text
observatory/audits/etapa_1_conformidade/evidencias/check/
```

Para uma execução limpa, remova apenas os relatórios antigos desse diretório;
não remova o diretório.

---

## 8. Veredito da etapa

| Afirmação                                             | Veredito                                          |
| ----------------------------------------------------- | ------------------------------------------------- |
| As 29 regras verificáveis são cumpridas               | **sustentada** (0 violações)                      |
| A ROF-003 é executada pelo `ProjectValidator`         | **não sustentada**                                |
| A ROF-003 tem implementação e teste unitário          | **sustentada**                                    |
| A persistência está organizada conforme as regras RED | **sustentada** (verificação `Dependency correct`) |
| O projeto está 100% conforme                          | **não sustentada** (ROF-003 sem scanner)          |
