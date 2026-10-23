# Relatório técnico — Etapa 6: manutenibilidade e evolutividade

**Projeto:** SOLAR
**Data:** 2026-10-23
**Status:** avaliação preliminar; estudo longitudinal **não executado**
**Código de produção alterado:** não

---

## 1. Pergunta e por que ela não é trivial

A pergunta é: **a arquitetura atual ajuda ou dificulta mudanças futuras?**

Ela não pode ser respondida apenas com métricas estáticas. Manutenibilidade
envolve:

- esforço para entender o código;
- esforço para localizar o que mudar;
- risco de regressão;
- custo de testar e validar;
- acoplamento entre mudanças;
- conhecimento dos mantenedores.

O MI do Radon cobre apenas uma parte pequena e enviesada disso. Por isso esta
etapa separa **evidência existente** de **protocolo planejado**.

---

## 2. Evidência existente

### 2.1 Índice de manutenibilidade (MI)

| Indicador                      | Valor                                    |
| ------------------------------ | ---------------------------------------- |
| Módulos medidos                | 269                                      |
| Módulos de produção            | 208                                      |
| Rank A                         | 269/269 (100%)                           |
| MI médio de produção           | 88,14                                    |
| MI mediano de produção         | 100                                      |
| Módulos de produção com MI 100 | **110 (52,9%)**                          |
| MI mínimo de produção          | 32,26                                    |
| Reprodutibilidade              | 269/269, 0 divergências                  |
| Sensibilidade a docstrings     | 26 módulos com delta > 10; máximo +47,62 |

**Interpretação:** o MI está saturado no topo. A causa é estrutural:

1. o volume Halstead é zero para mais da metade das funções, porque o visitante
   do Radon não conta chamadas/atributos;
2. docstrings contam como comentários, elevando o termo senoidal;
3. o MI é uma fórmula composta, não uma medida de esforço de manutenção.

**Conclusão:** o MI é **reproduzível**, mas **não discriminante**. Não deve ser
usado para ranking nem para afirmar “fácil de manter”.

### 2.2 Superfície não exercitada

- 15 módulos fora do fluxo estático;
- 631 SLOC (10,08% da produção);
- inclui CSRF, rate limit, brute force, `UrlGuard`, `token`, upload, a Rule
  ROF-003, `responsibility_contract`, `observatory.log` (pacote-pai) e
  `user_repository`.

**Interpretação:** pode ser API preparada, subsistema opcional ou dívida de
integração. O dado não decide qual.

### 2.3 Estrutura

- 208 módulos, 306 arestas, 0 ciclos estáticos;
- 90,2% das arestas intra-camada;
- Ce mediano 3; Ca mediano 1;
- 1 ciclo dinâmico com dependência de ordem.

**Interpretação:** a estrutura é compatível com evolução modular, mas
**compatibilidade não é demonstração**. Um baixo acoplamento pode coexistir com
processos de mudança ruins.

---

## 3. O que não foi medido

| Dimensão                  | Por que importa                      | Status                                                                         |
| ------------------------- | ------------------------------------ | ------------------------------------------------------------------------------ |
| Cobertura de linha/ramo   | saber o que os testes exercitam      | **não medido** (a suíte tem 587 testes passando, mas cobertura não foi medida) |
| Mutation score            | saber se os testes detectam defeitos | **não medido**                                                                 |
| Change coupling           | saber quais arquivos mudam juntos    | **não medido**                                                                 |
| Lead time de mudança      | esforço real de evolução             | **não medido**                                                                 |
| Defeitos pós-merge        | risco de regressão                   | **não medido**                                                                 |
| Estudo com mantenedores   | custo cognitivo real                 | **não medido**                                                                 |
| Série histórica           | tendência                            | **não medido**                                                                 |
| Idade/CVE de dependências | risco de evolução                    | **não medido**                                                                 |

---

## 4. Protocolo de avaliação (planejado)

### 4.1 Cenários de mudança

Executar 5–8 tarefas equivalentes, com o mesmo enunciado para todas as
arquiteturas comparadas:

1. adicionar um campo ao Model e expô-lo no Resource;
2. adicionar um endpoint CRUD;
3. adicionar uma validação de domínio;
4. trocar a persistência de um Model;
5. adicionar autenticação a uma rota;
6. adicionar uma nova regra arquitetural;
7. corrigir um bug de contrato;
8. remover um módulo não utilizado.

Para cada tarefa, medir:

- tempo até o primeiro commit;
- tempo total;
- arquivos tocados;
- linhas alteradas;
- retrabalho (commits de correção);
- defeitos encontrados em revisão/teste;
- necessidade de mudança em arquivos “distantes”.

### 4.2 Métricas contínuas

| Métrica              | Definição                           | Fonte             |
| -------------------- | ----------------------------------- | ----------------- |
| Change coupling      | arquivos que co-mudam em uma janela | histórico Git     |
| Lead time            | abertura → merge                    | issues/PRs        |
| Defect density       | defeitos ÷ KLOC                     | issues            |
| Cobertura            | linha/ramo                          | coverage          |
| Mutation score       | mutantes mortos ÷ total             | mutmut/cosmic-ray |
| Dependency freshness | versões atrasadas/CVEs              | pip-audit         |
| Architecture fitness | violações por release               | `solar check`     |

### 4.3 Estudo com mantenedores

- mínimo de 5 participantes por arquitetura;
- tarefas de compreensão e correção cronometradas;
- mesmo enunciado e mesmo ambiente;
- análise por tempo, acertos e esforço subjetivo (NASA-TLX ou similar);
- evitar que o autor da arquitetura seja o único participante.

### 4.4 Critérios de aceite

| Dimensão        | Critério mínimo                                        |
| --------------- | ------------------------------------------------------ |
| Cobertura       | ≥ 80% de linha nos módulos críticos                    |
| Mutation        | ≥ 60% nos módulos críticos                             |
| Change coupling | nenhum par inesperado acima do limiar definido         |
| Fitness         | 0 violações nas regras executadas; ROF-003 com scanner |
| Lead time       | comparável ou melhor que a linha de base               |
| Estudo humano   | amostra ≥ 5, com relatório de incerteza                |

---

## 5. Ameaças à validade

1. **Viés do autor:** quem projeta a arquitetura tende a defendê-la.
2. **Tarefas não representativas:** cenários escolhidos podem favorecer um
   estilo.
3. **Experiência dos participantes:** diferença de familiaridade confunde o
   resultado.
4. **Tamanho da amostra:** 5 participantes não generaliza.
5. **Ambiente:** hardware, sistema e ferramentas precisam ser iguais.
6. **Medida de cobertura:** cobertura não é eficácia.
7. **MI saturado:** não usar como desfecho principal.
8. **Histórico curto:** uma fotografia não mostra tendência.

---

## 6. Conclusão

A evidência existente permite dizer:

- o MI é alto, mas **não discrimina**;
- a estrutura tem baixo acoplamento e separação por camadas;
- há 15 módulos fora do fluxo estático;
- não há estudo de mudança, cobertura, mutação ou histórico.

Portanto, a resposta honesta é: **a arquitetura é plausivelmente evolutiva, mas
a evolutividade não foi demonstrada**. O protocolo acima é o mínimo para
transformar plausibilidade em evidência.

---

## 7. Veredito da etapa

| Afirmação                             | Veredito                    |
| ------------------------------------- | --------------------------- |
| O MI é reproduzível                   | **sustentada**              |
| O MI mede manutenibilidade            | **não sustentada**          |
| A estrutura é compatível com evolução | **sustentada**              |
| A arquitetura é evolutiva             | **não demonstrada**         |
| Há dívida crescente                   | **não sustentada**          |
| Há superfície não exercitada          | **sustentada** (15 módulos) |
