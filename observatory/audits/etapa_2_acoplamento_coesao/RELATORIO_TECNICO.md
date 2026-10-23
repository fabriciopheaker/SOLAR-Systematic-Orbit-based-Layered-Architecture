# Relatório técnico — Etapa 2: acoplamento, coesão e dependências

**Projeto:** SOLAR
**Data da análise:** 2026-10-23
**Corpus:** 208 módulos de produção; 61 módulos de teste
**Ferramentas:** AST do Python 3.14.7, Radon 6.0.1, script próprio
`solar_metrics.py`
**Código de produção alterado:** não

---

## 1. Pergunta e escopo

A pergunta é estrutural: **como o código de produção se organiza em módulos e
classes, e quais dependências essa organização cria?**

Foram medidas:

- fan-out (Ce) e fan-in (Ca) por módulo;
- instabilidade `I = Ce / (Ca + Ce)`;
- arestas internas e distribuição por camada;
- componentes fortemente conexos (Tarjan) e ciclos;
- CBO por classe (aproximação por AST);
- LCOM1, LCOM4, TCC e aplicabilidade;
- alcançabilidade a partir dos pontos de entrada.

**Fora do escopo:** complexidade de controle (etapa 3), desempenho (etapa 4),
segurança (etapa 5) e evolução histórica (etapa 6).

---

## 2. Corpus e definições

| Conjunto  | Arquivos | SLOC       | Funções/métodos | Classes |
| --------- | -------- | ---------- | --------------- | ------- |
| Produção  | 208      | 6.265      | 553             | 136     |
| Testes    | 61       | 5.529      | 680             | 29      |
| **Total** | **269**  | **11.794** | **1.233**       | **165** |

Definições:

- **Ce:** número de módulos internos distintos importados por um módulo.
- **Ca:** número de módulos internos de produção que importam um módulo.
- **I:** `Ce / (Ca + Ce)`; indefinida quando `Ca + Ce = 0`.
- **Aresta interna:** import entre módulos do projeto, incluindo imports
  diferidos e imports dinâmicos verificáveis.
- **Densidade:** arestas observadas ÷ arestas possíveis (`n · (n − 1)`).

Exclusões: `.git`, `__pycache__`, `.pytest_cache`, `htmlcov`, `docs`, `docker`,
`storage/` de primeiro nível e `observatory/audits/`. A suíte em
`observatory/tests/` entra como corpus de teste, nunca como produção.

---

## 3. Fan-in, fan-out e instabilidade

### 3.1 Distribuição

| Métrica | N   | Mín. | Mediana | Média | P90 | Máx.   |
| ------- | --- | ---- | ------- | ----- | --- | ------ |
| Ce      | 101 | 1    | **3**   | 3,03  | 4   | **49** |
| Ca      | 138 | 1    | **1**   | 2,22  | 3   | **38** |

- **107 módulos** têm Ce zero (não importam outro módulo interno).
- **70 módulos** têm Ca zero (não são importados por produção).
- **60 módulos** têm `I` indefinida (`Ca + Ce = 0`).

### 3.2 Maiores valores

| Módulo                                | Ce  | Ca     | I     | Papel                           |
| ------------------------------------- | --- | ------ | ----- | ------------------------------- |
| `nucleus.rules.project_validator`     | 49  | 2      | 0,961 | registro explícito de 29 regras |
| `nucleus.kernel`                      | 16  | 1      | 0,941 | composition root                |
| `nucleus.middleware.request_pipeline` | 6   | —      | —     | pipeline de requisição          |
| `nucleus.database.database`           | 5   | 8      | 0,385 | fachada + imports dinâmicos     |
| `nucleus.exceptions.solar_exception`  | 0   | **38** | 0,000 | exceção-base                    |
| `nucleus.rules.rule`                  | 0   | **32** | 0,000 | contrato abstrato               |

**Interpretação:** fan-out alto em `project_validator` e `kernel` é
**estrutural e intencional**. O risco é de manutenção: cada nova regra exige
edição do validador (ponto único de registro). `solar_exception` é um hub
estável, com contrato pequeno e ampla reutilização.

---

## 4. Dependências, camadas e ciclos

### 4.1 Distribuição por camada

| De → Para                         | Arestas |
| --------------------------------- | ------- |
| Nucleus → Nucleus                 | 255     |
| Orbits/Planets → Orbits/Planets   | 12      |
| Orbits/Planets → Nucleus          | 11      |
| Observatory → Observatory         | 7       |
| Orbits → Orbits/Planets           | 4       |
| Bootstrap → Nucleus               | 3       |
| Orbits/Planets → Orbits/Database  | 3       |
| Bootstrap → Observatory           | 2       |
| Observatory → Nucleus             | 2       |
| Orbits/Database → Nucleus         | 2       |
| Orbits/Database → Orbits/Database | 2       |
| Nucleus → Orbits                  | 1       |
| Nucleus → Orbits/Database         | 2       |
| **Total**                         | **306** |

Arestas intra-camada: **276 (90,2%)**. Entre camadas: **30 (9,8%)**.

### 4.2 Ciclos

| Grafo                           | Arestas | Ciclos | SCCs             |
| ------------------------------- | ------- | ------ | ---------------- |
| Apenas estático                 | 304     | **0**  | 207 para 208 nós |
| Estático + dinâmico verificável | 306     | **1**  | —                |

Ciclo único:

```text
nucleus.database.database → orbits.database.models.user_model
orbits.database.models.user_model → nucleus.database.database
```

Evidência:

- `nucleus/database/database.py:167` importa Models dinamicamente;
- `orbits/database/models/user_model.py:2` importa `Database`;
- `orbits/database/models/user_model.py:5` usa `Database.orm` no momento do
  import.

**Interpretação:** é um ciclo **intencional e controlado**, mas cria dependência
de ordem. Usar o Model antes de `Database.init()` falha com
`AttributeError: 'NoneType' object has no attribute 'Column'`. Não foi
classificado como defeito; é um risco de acoplamento temporal.

---

## 5. CBO por classe

**Método:** aproximação por AST. Nomes resolvidos por imports; nomes livres
apenas quando únicos no projeto; CBO interno = classes do projeto; CBO externo
heurístico.

| Estatística | Valor             |
| ----------- | ----------------- |
| Classes     | 136               |
| Média       | 1,54              |
| Mediana     | 1                 |
| P90         | 3                 |
| Máximo      | **15** (`Kernel`) |
| Soma        | 210               |

Maiores: `Kernel` 15, `RequestPipeline` 6, `ProjectValidator` 5,
`Broadcast` 4, `Server` 4.

**Limitação:** não resolve tipos, injeção por atributo, fábricas ou `getattr`.
É comparável dentro do projeto, não com CBO de ferramentas tipadas.

---

## 6. Coesão

### 6.1 Aplicabilidade

| Situação                              | Classes        |
| ------------------------------------- | -------------- |
| LCOM aplicável                        | **39 (28,7%)** |
| N/A — menos de 2 métodos de instância | 54             |
| N/A — sem atributos de instância      | 42             |
| N/A — nenhum método usa estado        | 1              |
| **Total**                             | **136**        |

### 6.2 Resultados (n = 39)

| Métrica | Mín. | Mediana  | Média | P90  | Máx. |
| ------- | ---- | -------- | ----- | ---- | ---- |
| LCOM1   | 0    | **3**    | 10,82 | 30   | 89   |
| LCOM4   | 1    | **1**    | 1,13  | 2    | 3    |
| TCC     | 0,00 | **0,30** | 0,40  | 1,00 | 1,00 |

**Interpretação:** LCOM1 alto em scanners reflete classes com **um único
atributo e muitos métodos**, não necessariamente baixa coesão de domínio.
LCOM4 permanece próximo de 1, indicando que os métodos formam poucos grupos
conectados. O dado não sustenta “a coesão é ruim”.

---

## 7. Alcançabilidade

| Indicador                                     | Valor                                  |
| --------------------------------------------- | -------------------------------------- |
| Pontos de entrada                             | `server`, `observatory.solar.__main__` |
| Módulos alcançáveis                           | 134 / 208                              |
| Módulos com código não alcançáveis (estático) | **15**                                 |
| SLOC não alcançável (estático)                | **631 (10,08%)**                       |
| Ausentes confirmados em runtime               | **14** (625 SLOC, 9,98%)               |
| Production SLOC                               | 6.265                                  |

Os 15 módulos incluem mecanismos de segurança não ligados (CSRF, rate limit,
brute force, `UrlGuard`, `token`), upload, a Rule ROF-003, `responsibility_contract`,
`observatory.log` (pacote-pai, refutado em runtime) e `user_repository`.

**Interpretação:** “não alcançável” ≠ “código morto”. O dado sustenta que esses
módulos não participam do fluxo executável atual; a intenção (API pública,
subsistema opcional ou dívida de integração) não é decidida pela métrica.

---

## 8. Auditoria dos 60 alertas originais

| Veredito                          | Quantidade |
| --------------------------------- | ---------- |
| Confirmado                        | 7          |
| Falso positivo                    | 7          |
| Parcial                           | 43         |
| Não reproduzível                  | 1          |
| Confirmado fora do escopo (teste) | 2          |

Causas principais das divergências:

- a ferramenta original mistura produção, testes e dependências externas;
- fan-in/fan-out incluem bibliotecas e testes;
- LCOM é aplicado a classes sem estado de instância;
- limiares não são declarados;
- um valor histórico não é reproduzível.

O CSV completo está em `dados/alertas_estruturais_revisados.csv`.

---

## 9. Limitações

1. **CBO é aproximação por AST**, sem resolução de tipos.
2. **Alcançabilidade é estática**; o tracing de runtime cobre três cenários e
   não requisições HTTP.
3. **LCOM não se aplica a 97 classes**; qualquer média sobre todas as classes
   seria enganosa.
4. **Densidade baixa não é mérito automático**: mede dispersão, não qualidade.
5. **Ciclo dinâmico** depende de ordem de importação; não foi testado sob todas
   as sequências de inicialização.
6. **O relatório original não é reproduzível como ferramenta**; apenas os
   valores recalculados são auditáveis.

---

## 10. Reprodução

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py
py observatory/audits/etapa_2_acoplamento_coesao/scripts/revisar_relatorio.py
py observatory/audits/etapa_2_acoplamento_coesao/evidencias/verificacoes_independentes.py
```

Saídas:

- `dados/` — acoplamento, coesão, ciclos, alcançabilidade;
- `../etapa_3_complexidade/dados/` — funções, Halstead, complexidade cognitiva;
- `evidencias/verificacoes.json` — recálculo independente.

---

## 11. Veredito da etapa

| Afirmação                                    | Veredito                                          |
| -------------------------------------------- | ------------------------------------------------- |
| O acoplamento interno é baixo e esparso      | **sustentada**                                    |
| Os hubs têm papel arquitetural               | **sustentada**                                    |
| Há 0 ciclos estáticos                        | **sustentada**                                    |
| Há 1 ciclo dinâmico com dependência de ordem | **sustentada**                                    |
| Há 15 módulos fora do fluxo estático         | **sustentada** (estático); incerta para o sistema |
| O CBO é absoluto                             | **não sustentada** (aproximação AST)              |
| A coesão é ruim                              | **não sustentada**                                |
