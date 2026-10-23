# Resumo executivo — auditoria da arquitetura SOLAR

**Data:** 2026-10-23
**Escopo:** código de produção da SOLAR, com auditorias estáticas, de runtime,
de segurança e de manutenibilidade
**Código de produção alterado:** não
**Natureza:** auditoria técnica reprodutível; não é certificação

---

## 1. Resposta curta

A SOLAR é uma arquitetura **pequena, estruturalmente coerente e de baixa
complexidade de controle**, com acoplamento interno baixo e separação clara de
camadas. Os problemas encontrados **não são de caos estrutural**; são de
**concorrência na escrita**, **superfície de segurança não protegida**,
**observabilidade frágil**, **cobertura de verificação incompleta** e
**evidência insuficiente de manutenibilidade**.

A conclusão mais importante é metodológica: os números atuais permitem decisões
melhores, mas **não autorizam dizer que a arquitetura é “boa” em termos
absolutos**, nem que é “100% conforme”.

---

## 2. O que foi feito

| Etapa                             | O que responde                           | Status                                                       |
| --------------------------------- | ---------------------------------------- | ------------------------------------------------------------ |
| 1. Conformidade                   | as regras declaradas são obedecidas?     | 29 regras, 0 violações; ROF-003 sem scanner                  |
| 2. Acoplamento/coesão             | como os módulos dependem uns dos outros? | 208 módulos, 306 arestas, 0 ciclos estáticos                 |
| 3. Complexidade                   | onde está o custo de leitura/decisão?    | 553 funções, CC mediana 2, 1 outlier cognitivo               |
| 4. Desempenho                     | como se comporta sob carga?              | 12 cenários, 1.860 requisições; falha de escrita concorrente |
| 5. Segurança/isolamento           | quais controles estão ativos?            | 33 testes; sem vulnerabilidade confirmada, mas riscos        |
| 6. Manutenibilidade/evolutividade | a arquitetura ajuda a mudar?             | preliminar; MI saturado; estudo longitudinal não executado   |
| Benchmark                         | SOLAR × Clean × MVC × Hexagonal          | plano e viabilidade; **sem resultados comparativos**         |

---

## 3. Achados principais

### 3.1 Estrutura

- **208 módulos**, **306 arestas internas**, densidade **0,71%**.
- **90,2%** das arestas são intra-camada.
- **0 ciclos estáticos**; **1 ciclo dinâmico** entre `Database` e `UserModel`.
- Hubs explicados pelo papel: `project_validator` (Ce 49), `Kernel` (CBO 15),
  `solar_exception` (Ca 38).
- **15 módulos fora do fluxo estático** (631 SLOC, 10,08%); o tracing de runtime confirma **14 ausentes** (625 SLOC, 9,98%) e refuta `observatory.log` como pacote-pai.

### 3.2 Complexidade

- **553 funções** de produção; CC mediana **2**; máximo **10**; **94,6% rank A**.
- Nenhuma função em rank C.
- Complexidade cognitiva: 300 funções, soma 794, máximo **18**; apenas
  `_destination` acima de 15.
- Halstead **não discrimina**: mais da metade das funções tem volume zero por
  limitação do Radon.

### 3.3 Desempenho

- `GET /solar/health`: 0 erros em concorrência 1–16; mediana de 5,45–9,24 ms
  (c1) a 75,92 ms (c16); vazão 87–204 req/s.
- `POST /examples/users`: mediana ~353 ms em c1, dominada por bcrypt.
- **Falha comprovada de escrita concorrente:** 2/20 em c2, 6/20 em c4 (30%);
  `sqlalchemy.exc.IllegalStateChangeError` por `Session` compartilhada.
- `c8` não executado por limite de segurança.

### 3.4 Segurança e isolamento

- Headers obrigatórios e bcrypt funcionam.
- Validação de presença e JSON funciona; **tipo e tamanho não**.
- `POST /examples/users` é **público**; não há autenticação/autorização.
- CSRF, rate limit, brute force, JWT e upload **inativos**.
- 404/405 são mascarados como **500**.
- SQL injection testada **não executou**; ORM parametrizada.
- Mass assignment **não aplicado**.
- `ErrorLog` falha sob concorrência; **0 erros registrados**.
- **Nenhuma vulnerabilidade confirmada** nos 33 cenários; há riscos potenciais.

### 3.5 Manutenibilidade e evolutividade

- MI reproduzido (269/269, 0 divergências), mas **saturado**: 110 de 208 módulos
  de produção com MI 100.
- MI **não serve como ranking** nem como prova de facilidade de manutenção.
- Não há estudo histórico, de cobertura, de mutação ou com mantenedores.
- **Evolutividade não demonstrada.**

---

## 4. A correção sobre a ROF-003

A frase “ROF-003 não é executada” é **verdadeira apenas para o
`ProjectValidator`**. A regra:

- existe como classe;
- tem teste unitário;
- não é registrada em `project_checks()`;
- **não** é uma regra de persistência.

A organização Model → Persistence → Repository é verificada pelas regras
RED-002, RED-003, RED-005, RED-006, RED-007 e RED-008, todas executadas. O
relatório `Dependency correct` confirma que a estrutura atual as satisfaz.

**Conclusão correta:** a conformidade é parcial porque falta scanner estático
para a ROF-003, não porque a persistência esteja desorganizada. “100% conforme”
não é sustentável, mas o motivo precisa ser dito com precisão.

---

## 5. O que os dados **não** sustentam

| Afirmação                                 | Por que não                            |
| ----------------------------------------- | -------------------------------------- |
| “A arquitetura é boa.”                    | Nenhuma métrica mede qualidade global. |
| “O código é fácil de manter.”             | MI saturado; sem estudo humano.        |
| “O desempenho é bom.”                     | Não há SLO; uma instância local.       |
| “A aplicação escala.”                     | Não testada.                           |
| “Os 15 módulos são código morto.”         | Ausência em cenário não prova desuso.  |
| “O ciclo causa falhas.”                   | Não houve falha atribuída ao ciclo.    |
| “A coesão é ruim.”                        | LCOM não se aplica a 97 classes.       |
| “Há SQL injection.”                       | O teste não executou o payload.        |
| “Há vulnerabilidade confirmada.”          | Nenhuma confirmada nos 33 testes.      |
| “SOLAR é melhor que Clean/MVC/Hexagonal.” | O benchmark não foi executado.         |

---

## 6. Prioridades recomendadas

| Prioridade | Ação                                                    | Por quê                        | Não fazer                                        |
| ---------- | ------------------------------------------------------- | ------------------------------ | ------------------------------------------------ |
| 1          | Corrigir a `Session` compartilhada                      | falha de escrita comprovada    | aumentar carga antes                             |
| 2          | Exigir auth/autorização no endpoint público, se exposto | risco de abuso                 | assumir “público por desenho” sem requisito      |
| 3          | Validar tipo e limitar tamanho                          | 500 e 64 KiB aceitos           | confundir com presença                           |
| 4          | Corrigir 404/405 → 500                                  | status incorreto               | tratar como erro de negócio                      |
| 5          | Corrigir `ErrorLog` sob concorrência                    | perda de observabilidade       | silenciar a falha                                |
| 6          | Implementar scanner da ROF-003                          | conformidade verificável       | declarar 100% antes                              |
| 7          | Medir cobertura/mutação e histórico                     | manutenibilidade sem evidência | usar MI como ranking                             |
| 8          | Executar o benchmark só após a fase 0                   | comparação justa               | publicar números sem implementações equivalentes |

---

## 7. Confiança

| Conclusão                              | Confiança                                 |
| -------------------------------------- | ----------------------------------------- |
| Estrutura de acoplamento e ciclos      | **alta** (AST + verificação independente) |
| Complexidade CC e tamanho              | **alta** (Radon reproduzido)              |
| Falha de escrita concorrente           | **alta** (HTTP + reprodução direta)       |
| Controles de segurança ativos/inativos | **alta** para o código inspecionado       |
| Ausência de vulnerabilidade            | **baixa** (33 testes, sem scanner)        |
| Manutenibilidade                       | **baixa** (MI saturado, sem estudo)       |
| Comparação entre arquiteturas          | **nenhuma** (não executada)               |

---

## 8. Conclusão

A SOLAR medida é uma arquitetura de **governança**: a maior parte do código e da
complexidade está no Nucleus, onde vivem as regras. Os Planets são pequenos e a
estrutura de dependências é disciplinada. O que merece atenção não é o número
alto de acoplamento — ele é explicado pelo papel dos componentes — mas:

1. a falha de escrita concorrente;
2. a superfície pública sem autenticação;
3. a ausência de validação de tipo/tamanho;
4. a observabilidade que falha sob carga;
5. a ROF-003 sem scanner;
6. a ausência de evidência de manutenibilidade e de comparação externa.

**A entrega correta é esta:** limites declarados, evidência reproduzível e
nenhuma conclusão além do que os dados permitem.
