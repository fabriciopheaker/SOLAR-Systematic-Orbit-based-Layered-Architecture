# SOLAR

## Systematic Orbit-based Layered Architecture

A **SOLAR — Systematic Orbit-based Layered Architecture** é uma arquitetura de software baseada na organização sistemática da aplicação em estruturas governamentais, operacionais, funcionais e de comunicação.

A SOLAR utiliza conceitos inspirados em um sistema orbital para representar a relação entre o núcleo arquitetural, os mecanismos de execução, os caminhos de acesso aos módulos e os próprios módulos funcionais.

A arquitetura é composta por sete conceitos principais:

1. **Nucleus**
2. **Atmosphere**
3. **Orbits**
4. **Planets**
5. **Environment**
6. **Observatory**
7. **Satellites**

---

# 1. Visão conceitual

```text
                              NUCLEUS
                         GOVERNANÇA DA SOLAR
                                │
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
              ATMOSPHERE               ENVIRONMENT
                    │
                    │
                    ▼
                 ORBITS
              ╭─────┼─────╮
              │     │     │
              ▼     ▼     ▼
             🪐    🪐    🪐
          PLANET PLANET PLANET
              │     │     │
              └─────┼─────┘
                    │
                SATELLITES
                    │
             ┌──────┴──────┐
             ▼             ▼
          PLANETS      EXTERNAL SERVICES

                    ▲
                    │
               OBSERVATORY
```

O **Nucleus** governa.

A **Atmosphere** fornece e controla os mecanismos de execução.

As **Orbits** representam as trajetórias arquiteturais.

Os **Planets** representam os módulos funcionais.

O **Environment** fornece as condições e recursos necessários para execução.

Os **Satellites** realizam comunicações entre módulos ou com serviços externos.

O **Observatory** observa a execução da aplicação.

---

# 2. Nucleus

O **Nucleus** é o cérebro arquitetural da SOLAR.

Ele define e governa:

- princípios;
- regras;
- contratos;
- políticas;
- invariantes;
- padrões arquiteturais;
- regras de segurança;
- regras de dependência;
- mecanismos fundamentais compartilhados.

O Nucleus não representa uma etapa do processamento de uma requisição.

Ele representa a **governança da aplicação**.

Atmosphere, Orbits e Planets devem respeitar as regras estabelecidas pelo Nucleus.

---

# 3. Atmosphere

A **Atmosphere** é responsável pelos mecanismos estruturais necessários para o funcionamento da aplicação.

Entre suas responsabilidades estão:

- recebimento de requests;
- routing;
- criação de contexto;
- validação;
- sanitização;
- autenticação;
- autorização;
- tratamento de exceções;
- tratamento de erros;
- serialização;
- persistência;
- criptografia;
- comunicação com infraestrutura;
- comunicação com recursos tecnológicos;
- preparação de responses.

A Atmosphere transforma as regras do Nucleus em mecanismos operacionais.

---

# 4. Orbits

As **Orbits** representam os caminhos ou trajetórias arquiteturais utilizados para alcançar os módulos funcionais.

Uma Orbit não é um módulo de negócio.

Ela representa o espaço arquitetural no qual um Planet é alcançado e executado.

```text
Atmosphere
     │
     ▼
   Orbit
     │
     ▼
  Planet
```

A Orbit também participa do retorno:

```text
Planet
   │
   ▼
 Orbit
   │
   ▼
Atmosphere
```

---

# 5. Planets

**Planets são a representação conceitual dos módulos funcionais da aplicação.**

Não existe uma camada física chamada `planets`.

Não existe obrigatoriamente uma pasta:

```text
planets/
```

Um Planet existe **dentro de uma Orbit**.

Por exemplo:

```text
Orbit
 │
 ├── Customer Planet
 ├── Order Planet
 └── Billing Planet
```

Os Planets representam unidades funcionais independentes da aplicação.

Exemplos:

- Customer;
- Product;
- Order;
- Billing;
- Employee.

Cada módulo possui suas próprias responsabilidades e regras de negócio.

---

# 6. Environment

O **Environment** representa o ambiente necessário para a aplicação funcionar.

Pode fornecer:

- configurações;
- variáveis de ambiente;
- identidade da aplicação;
- conexões;
- credenciais;
- secrets;
- configurações criptográficas;
- informações de infraestrutura;
- configurações de serviços externos.

O Environment fornece recursos.

O Nucleus define as regras que determinam como esses recursos devem ser utilizados.

---

# 7. Observatory

O **Observatory** é responsável pela observabilidade da aplicação.

Ele permite acompanhar o comportamento do sistema durante sua execução.

Pode registrar ou acompanhar:

- requests;
- responses;
- erros;
- exceções;
- traces;
- métricas;
- eventos;
- auditoria;
- eventos de segurança;
- desempenho.

O Observatory observa o sistema sem assumir a responsabilidade pela execução das regras de negócio.

---

# 8. Satellites

Os **Satellites** representam os mecanismos de comunicação utilizados quando um Planet precisa se comunicar com algo que está fora de seu próprio limite funcional.

Um Satellite pode conectar:

```text
Planet → Planet
```

ou:

```text
Planet → External Service
```

Exemplos:

```text
Customer
   │
   ▼
Satellite
   │
   ▼
Billing
```

ou:

```text
Order
   │
   ▼
Payment Satellite
   │
   ▼
Payment API
```

O Satellite impede que o Planet precise conhecer diretamente a infraestrutura ou implementação do destino.

---

# 9. Fluxo de uma requisição

O fluxo principal de uma operação é:

```text
                    REQUEST
                       │
                       ▼
                 ATMOSPHERE
                       │
                routing / control
                       │
                       ▼
                    ORBIT
                       │
                trajectory
                       │
                       ▼
                    PLANET
                       │
                 business logic
                       │
                       ├──────────────┐
                       │              │
                       ▼              ▼
                   ORBIT          SATELLITE
                                      │
                              Planet / Service
                                      │
                                      ▼
                                   result
                       │
                       ▼
                    ORBIT
                       │
                       ▼
                 ATMOSPHERE
                       │
                response control
                       │
                       ▼
                   RESPONSE
```

O Nucleus não aparece como uma etapa do fluxo.

Ele governa todo o processo.

---

# 10. Governança do Nucleus

A relação do Nucleus com as demais estruturas é de governança e dependência arquitetural.

```text
                       NUCLEUS
                    ┌────┼────┐
                    │    │    │
                 governs governs governs
                    │    │    │
                    ▼    ▼    ▼
             ATMOSPHERE ORBITS PLANETS
```

A aplicação não deve interpretar o Nucleus como middleware.

O Nucleus é o conjunto de leis sob as quais a aplicação opera.

---

# 11. Comunicação

A comunicação entre componentes deve respeitar os limites arquiteturais.

```text
PLANET
  │
  ▼
SATELLITE
  │
  ├──────────► PLANET
  │
  └──────────► EXTERNAL SERVICE
```

O Planet não deve assumir diretamente detalhes de infraestrutura do destino.

---

# 12. Princípios fundamentais

A SOLAR estabelece como princípios fundamentais:

### 12.1 Negação como regra

Operações devem ser negadas por padrão quando não houver autorização explícita.

```text
DENY BY DEFAULT
```

### 12.2 Entrada externa não é confiável

Toda entrada externa deve ser tratada como potencialmente não confiável.

```text
NEVER TRUST EXTERNAL INPUT
```

### 12.3 Toda entrada deve ser validada

Dados recebidos pela aplicação devem passar pelos mecanismos apropriados de validação.

### 12.4 Toda saída deve ser controlada

Dados destinados ao exterior devem ser tratados antes de serem retornados.

### 12.5 Exceções devem ser tratadas

Exceções não devem escapar da arquitetura sem tratamento adequado.

### 12.6 Segurança é estrutural

Segurança não deve ser adicionada apenas como funcionalidade opcional.

Ela deve fazer parte da própria arquitetura.

### 12.7 Independência modular

Planets devem possuir limites funcionais claros e não devem depender diretamente da implementação interna de outros Planets.

### 12.8 Conformidade arquitetural

As regras estabelecidas pelo Nucleus devem poder ser verificadas.

---

# 13. Resumo

| Elemento        | Responsabilidade                                   |
| --------------- | -------------------------------------------------- |
| **Nucleus**     | Governança, leis, contratos e regras arquiteturais |
| **Atmosphere**  | Mecanismos estruturais e controle da execução      |
| **Orbit**       | Trajetória arquitetural até um módulo              |
| **Planet**      | Representação conceitual de um módulo funcional    |
| **Environment** | Ambiente e recursos necessários à execução         |
| **Observatory** | Observabilidade e acompanhamento da execução       |
| **Satellite**   | Comunicação entre módulos ou com serviços externos |

A SOLAR pode ser resumida conceitualmente como:

> **Nucleus governa. Atmosphere controla. Orbits conduzem. Planets executam. Satellites comunicam. Environment sustenta. Observatory observa.**
