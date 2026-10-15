# Nucleus

### 1. Definição

O Nucleus é o cérebro arquitetural da SOLAR.

Ele concentra as definições que controlam a arquitetura como um todo.

Seu papel é estabelecer as regras que todas as demais estruturas devem respeitar.

O Nucleus não representa um estágio do processamento.

Ele representa a governança.

### 2. Responsabilidades

O Nucleus é responsável por definir:

princípios;
contratos;
políticas;
regras arquiteturais;
regras de segurança;
regras de dependência;
invariantes;
padrões;
identidade arquitetural;
fundamentos compartilhados.

### 3. Não responsabilidades

Não pertencem ao Nucleus:

regras específicas de negócio;
acesso direto ao banco;
chamadas HTTP;
integração com APIs externas;
código específico do Flask;
implementação de módulos;
lógica de apresentação;
infraestrutura específica.

### 4. Dependência

A direção conceitual é:

ATMOSPHERE ──────► NUCLEUS

PLANETS ─────────► NUCLEUS

O inverso não deve ocorrer:

NUCLEUS ──X──► ATMOSPHERE
NUCLEUS ──X──► PLANET
