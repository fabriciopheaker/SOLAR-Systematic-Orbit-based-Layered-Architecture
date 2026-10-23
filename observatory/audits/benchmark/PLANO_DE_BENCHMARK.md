# Plano de benchmark — SOLAR × Clean Architecture × MVC × Hexagonal

**Versão:** 1.0
**Data:** 2026-10-23
**Status:** plano; nenhuma execução comparativa realizada
**Autor:** auditoria da arquitetura SOLAR

---

## 1. Pergunta de pesquisa

**Pergunta principal:** em um mesmo sistema de referência, com funcionalidades e
ambiente controlados, quais são os trade-offs mensuráveis entre SOLAR, Clean
Architecture, MVC e Hexagonal em:

1. desempenho sob carga;
2. custo de mudança e evolutividade;
3. qualidade estrutural;
4. esforço de compreensão por mantenedores?

**Hipótese nula (H0):** não há diferença prática entre as arquiteturas nas
métricas definidas, após controle de implementação, ambiente e tarefa.

**Hipóteses alternativas (exploratórias):**

- H1: SOLAR e Hexagonal têm maior custo inicial, mas menor acoplamento de
  mudança em cenários de troca de infraestrutura.
- H2: MVC tem menor custo inicial e maior acoplamento em cenários de regra de
  negócio.
- H3: Clean Architecture tem melhor isolamento de framework, com maior número
  de arquivos e indireções.
- H4: as diferenças de desempenho são dominadas pela implementação (hash,
  banco, serialização), não pelo estilo arquitetural.

O estudo deve ser capaz de **refutar** cada hipótese, não apenas confirmá-la.

---

## 2. Definições operacionais

“Arquitetura” aqui não é um diagrama; é um conjunto de restrições verificáveis.

| Estilo                 | Regras operacionais mínimas                                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **SOLAR**              | Nucleus/Atmosphere/Orbits/Planets/Observatory; Controller → UseCase → Repository → Persistence → Database; regras RED/ROF/SEG verificáveis |
| **Clean Architecture** | Entities, Use Cases, Interface Adapters, Frameworks & Drivers; dependências apontam para dentro; regra de dependência verificável          |
| **MVC**                | Model, View, Controller; controller coordena model e view; sem camada de use case obrigatória                                              |
| **Hexagonal**          | domínio no centro; portas (interfaces) e adaptadores; dependências externas via portas                                                     |

Cada implementação deve declarar um **mapa de camadas** e um **conjunto de
regras de fitness** que possam ser verificadas automaticamente. O benchmark não
compara “intenção”; compara restrições efetivamente aplicadas.

---

## 3. Sistema de referência

### 3.1 Funcionalidades congeladas

Todas as versões devem implementar exatamente:

1. `GET /health` — status da aplicação;
2. `POST /users` — criar usuário com nome, e-mail e senha;
3. `GET /users/{id}` — consultar usuário (sem expor senha);
4. `POST /auth/login` — autenticar e devolver token;
5. `GET /users?email=` — buscar por e-mail;
6. `POST /files` — upload de arquivo com limite e tipo permitido;
7. `PATCH /users/{id}` — atualizar nome;
8. `DELETE /users/{id}` — exclusão lógica.

### 3.2 Regras de negócio comuns

- e-mail único e normalizado;
- senha com hash bcrypt;
- validação de presença, tipo e tamanho;
- erros com status HTTP correto (400/401/404/409/500);
- autenticação obrigatória nas rotas de escrita, exceto `POST /users`;
- log de erro sem vazamento de detalhe interno;
- nenhuma resposta expõe senha/hash.

### 3.3 Banco e dependências

- mesmo SGBD (SQLite para o harness; PostgreSQL como validação externa);
- mesmas versões de Python, Flask, SQLAlchemy, bcrypt;
- mesmas migrações e seeds;
- mesmo cliente HTTP e mesmo gerador de carga.

---

## 4. Desenho experimental

### 4.1 Fatores

| Fator       | Níveis                              |
| ----------- | ----------------------------------- |
| Arquitetura | SOLAR, Clean, MVC, Hexagonal        |
| Carga       | c1, c2, c4, c8, c16                 |
| Cenário     | health, create, read, login, upload |
| Repetição   | ≥ 5 por célula                      |

### 4.2 Variáveis controladas

- hardware, sistema operacional, versão de Python e bibliotecas;
- banco, schema, seeds e tamanho do dataset;
- limites de conexão e configuração do servidor;
- aquecimento e duração;
- dados sintéticos idênticos;
- logs desligados ou no mesmo nível;
- monitoramento com o mesmo overhead.

### 4.3 Variáveis dependentes

**Desempenho:**

- latência P50/P95/P99;
- vazão (req/s);
- taxa de erro;
- CPU por núcleo;
- memória (RSS médio/máximo);
- tempo de startup.

**Estrutura:**

- Ce/Ca, instabilidade;
- ciclos estáticos e dinâmicos;
- CBO (com ressalva de método);
- LCOM aplicável, LCOM4, TCC;
- CC, complexidade cognitiva;
- MI (apenas descritivo; não ranking);
- número de módulos, arquivos e linhas.

**Evolução:**

- tempo até o primeiro commit;
- tempo total da tarefa;
- arquivos tocados;
- linhas alteradas;
- retrabalho;
- defeitos em revisão/teste;
- distância entre o ponto de mudança e os arquivos alterados.

**Testes:**

- cobertura de linha e ramo;
- mutation score;
- tempo de execução da suíte;
- flakiness.

**Compreensão:**

- tempo para localizar o ponto de mudança;
- tempo para explicar o fluxo;
- acertos em perguntas de compreensão;
- carga subjetiva (NASA-TLX).

---

## 5. Cenários de mudança

Cada participante recebe o mesmo enunciado, no mesmo repositório base, com o
mesmo tempo máximo.

| ID  | Tarefa                                                  | O que mede                    |
| --- | ------------------------------------------------------- | ----------------------------- |
| M1  | adicionar campo `phone` ao usuário, do banco à resposta | propagação de mudança         |
| M2  | adicionar `GET /users/{id}`                             | custo de novo endpoint        |
| M3  | adicionar validação de força de senha                   | localização de regra          |
| M4  | trocar SQLite por PostgreSQL                            | isolamento de infraestrutura  |
| M5  | exigir autenticação em `PATCH`                          | composição de segurança       |
| M6  | adicionar nova regra de arquitetura                     | extensibilidade da governança |
| M7  | corrigir bug de contrato de saída                       | clareza de contrato           |
| M8  | remover upload não usado                                | acoplamento e limpeza         |

Cada tarefa deve ter **critérios de aceite automatizados** e um teste de
regressão. Sem isso, o tempo mede digitação, não arquitetura.

---

## 6. Protocolo de execução

### Fase 0 — Preparação (2–3 semanas)

1. Congelar a especificação funcional.
2. Implementar as quatro versões.
3. Criar o harness comum de carga e o runner de cenários.
4. Criar o dataset sintético e as seeds.
5. Definir SLOs e critérios de aceite.
6. Revisar as implementações com alguém que não as escreveu.

### Fase 1 — Piloto (1 semana)

1. Rodar 1 repetição por célula.
2. Verificar se o harness é justo.
3. Corrigir diferenças de configuração.
4. Estimar variabilidade e tamanho amostral.

### Fase 2 — Execução (2–3 semanas)

1. Randomizar a ordem das arquiteturas e cenários.
2. ≥ 5 repetições por célula.
3. Registrar ambiente, versões, seeds e logs.
4. Não alterar código entre repetições.

### Fase 3 — Estudo humano (2–3 semanas)

1. ≥ 5 participantes por arquitetura.
2. Mesmas tarefas e mesmo tempo.
3. Medir tempo, acertos e carga subjetiva.
4. Analisar com intervalos de confiança.

### Fase 4 — Análise e publicação (1–2 semanas)

1. Estatística descritiva e intervalos.
2. Testes não paramétricos (Mann-Whitney) ou bootstrap.
3. Tamanho de efeito (Cliff's delta / rank-biserial).
4. Correção para múltiplas comparações.
5. Relatório com dados brutos e código.

**Esforço total estimado:** 8–12 semanas, 2–3 pessoas, com pelo menos uma
pessoa independente das implementações.

---

## 7. Análise estatística

- **Não usar média isolada:** latência é assimétrica; usar mediana e
  percentis.
- **Intervalos de confiança:** bootstrap de 10.000 reamostragens.
- **Comparações:** Mann-Whitney U para duas arquiteturas; Kruskal-Wallis para
  quatro, com post-hoc corrigido.
- **Tamanho de efeito:** Cliff's delta ou rank-biserial.
- **Múltiplas comparações:** Holm-Bonferroni.
- **Significância prática:** definir antes um limiar mínimo (ex.: 10% de
  latência ou 1 arquivo de mudança).
- **Poder:** calcular com o piloto; se a variabilidade for alta, aumentar
  repetições.

---

## 8. Critérios de validade

O estudo só pode ser publicado se:

1. as quatro implementações passarem no **mesmo** conjunto de testes de
   aceitação;
2. o mapa de camadas e as regras de fitness forem verificáveis;
3. o harness for o mesmo;
4. o ambiente for documentado e reproduzível;
5. os dados brutos forem publicados;
6. as ameaças à validade forem declaradas;
7. nenhuma implementação for otimizada apenas para o benchmark;
8. o autor de uma implementação não for o único avaliador.

---

## 9. Ameaças à validade

| Tipo        | Ameaça                                        | Mitigação                        |
| ----------- | --------------------------------------------- | -------------------------------- |
| Construção  | “Arquitetura” definida de forma vaga          | regras operacionais e fitness    |
| Interna     | implementações com funcionalidades diferentes | testes de aceitação comuns       |
| Interna     | hardware/ambiente diferente                   | mesmo host, container ou VM      |
| Interna     | ordem dos testes influencia                   | randomização                     |
| Externa     | tarefas não representativas                   | 8 cenários + revisão por pares   |
| Externa     | uma linguagem/framework favorece um estilo    | mesma stack                      |
| Conclusão   | amostra pequena                               | ≥ 5 repetições + IC              |
| Conclusão   | MI saturado                                   | não usar como desfecho principal |
| Pesquisador | viés do autor                                 | avaliador independente           |
| Publicação  | resultados negativos não reportados           | pré-registro do plano            |

---

## 10. Pacote de reprodutibilidade

```text
benchmark/
├── especificacao/          # contrato funcional congelado
├── implementacoes/
│   ├── solar/
│   ├── clean/
│   ├── mvc/
│   └── hexagonal/
├── harness/                # carga, cenários, seeds
├── tarefas/                # M1–M8, critérios de aceite
├── dados/                  # resultados brutos, ambiente, logs
├── analise/                # scripts estatísticos
└── RELATORIO.md
```

Cada execução deve gravar:

- commit SHA de cada implementação;
- versões de Python e bibliotecas;
- hardware e sistema;
- seed e dataset;
- comando exato;
- arquivo bruto por requisição;
- hash dos artefatos.

---

## 11. O que conta como sucesso

Não é “provar que SOLAR é melhor”. É produzir evidência que permita dizer, com
incerteza declarada:

- em quais cenários cada estilo tem menor latência;
- em quais cenários cada estilo exige menos mudanças;
- qual é o custo inicial de cada estilo;
- qual é o custo de mudança de infraestrutura;
- qual é o esforço de compreensão;
- quais trade-offs são robustos e quais dependem do contexto.

Se os dados não mostrarem diferença prática, essa também é uma conclusão válida.

---

## 12. Estado atual

| Item                      | Estado            |
| ------------------------- | ----------------- |
| Pergunta e hipóteses      | definidas         |
| Definições operacionais   | definidas         |
| Sistema de referência     | especificado      |
| Cenários de mudança       | definidos         |
| Métricas                  | definidas         |
| Análise estatística       | definida          |
| Implementações comparadas | **não existem**   |
| Harness comum             | **não existe**    |
| Execução                  | **não realizada** |
| Resultados                | **nenhum**        |

**Próximo passo real:** implementar as quatro versões e o harness; só depois
executar. Sem isso, qualquer tabela comparativa seria fabricação.
