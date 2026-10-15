# Orbits

### 1. Definição

Uma Orbit representa uma trajetória arquitetural.

Ela conduz uma operação da Atmosphere até o Planet responsável pela funcionalidade.

ATMOSPHERE
│
▼
ORBIT
│
▼
PLANET

### 2. Orbit não é módulo

Uma Orbit não representa diretamente o módulo de negócio.

O módulo é o Planet.

Orbit
│
└── 🪐 Planet

Por isso, não deve existir necessariamente uma estrutura física:

planets/

O Planet existe conceitualmente dentro da Orbit.

### 3. Responsabilidades

A Orbit deve:

representar o caminho arquitetural;
preservar limites funcionais;
conduzir operações até o Planet;
permitir retorno controlado;
respeitar as regras do Nucleus;
impedir acesso arquitetural indevido.

### 4. Fluxo

Request
│
▼
Atmosphere
│
▼
Orbit
│
▼
Planet
│
▼
Orbit
│
▼
Atmosphere
│
▼
Response

### 5. Orbit e Satellite

Orbit e Satellite possuem funções diferentes.

Orbit

Conduz a operação até o módulo.

Atmosphere
↓
Orbit
↓
Planet
Satellite

Permite comunicação com outro módulo ou serviço externo.

Planet
↓
Satellite
↓
Planet / Service

Portanto:

Orbit conduz. Satellite comunica.
