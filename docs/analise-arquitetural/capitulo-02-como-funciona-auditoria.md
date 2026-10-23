# Capítulo 2 — Como funciona uma auditoria arquitetural

> **Pergunta deste capítulo:** quais são as abordagens de análise, o que cada uma revela e o que ela **não** garante?

---

## 2.1 Auditoria não é um único comando

Uma auditoria arquitetural é um **processo**. Ela começa com uma pergunta, escolhe evidências adequadas, executa medições, valida os resultados e interpreta no contexto. Não existe uma ferramenta única que responda “esta arquitetura é boa?”.

O processo usado no SOLAR teve cinco frentes:

1. **Análise estática** do código (AST) para dependências, classes, métodos e atributos.
2. **Métricas automatizadas** com Radon e com o plugin de complexidade cognitiva.
3. **Análise de grafos** para dependências, ciclos e alcançabilidade.
4. **Auditoria dos relatórios existentes** e recálculo independente.
5. **Análise dinâmica** por rastreamento de importações em runtime.

Cada frente responde a perguntas diferentes. Nenhuma, sozinha, cobre tudo.

---

## 2.2 Análise estática

**Análise estática** examina o código sem executá-lo. Em Python, a forma mais comum é ler o arquivo e construir uma **AST** — _Abstract Syntax Tree_ (Árvore Sintática Abstrata): uma representação em árvore das instruções do programa.

Exemplo: o trecho

```python
if total > 10:
    aplicar_desconto()
```

vira uma árvore com um nó `If`, uma condição (`Compare`) e um corpo (`Expr` com uma chamada). A AST permite responder:

- quais módulos são importados;
- quais classes existem;
- quais métodos cada classe tem;
- quais atributos cada método acessa;
- quais funções têm decisões e loops.

**Vantagens:** não precisa de banco, servidor ou configuração; é rápida e reproduzível; cobre todo o código, inclusive caminhos que nunca executam.

**Limitações:** não vê imports dinâmicos (`importlib.import_module`), não vê dependências criadas por plugins, não resolve tipos e pode errar quando o código usa `getattr`, fábricas ou reflexão. O SOLAR tem exatamente um caso relevante de import dinâmico de Models; um analisador puramente estático não o enxerga.

---

## 2.3 Análise dinâmica

**Análise dinâmica** observa o programa **durante a execução**. Ela responde a perguntas como:

- quais módulos foram realmente carregados?
- em que ordem?
- qual caminho de chamada provocou o carregamento?
- quais partes nunca foram exercitadas em um cenário?

No SOLAR, a análise dinâmica foi feita com:

- `sys.addaudithook` para registrar eventos de importação;
- um wrapper de `importlib.import_module` para capturar imports dinâmicos;
- comparação de `sys.modules` antes e depois de cada cenário.

**Vantagens:** mostra o que acontece de fato, incluindo dependências que a AST não vê.

**Limitações:** cobre apenas os cenários executados. Não carregar um módulo em um cenário não prova que ele nunca seja usado. Além disso, a instrumentação pode não ver tudo: o evento de auditoria `import` **não** é emitido por `importlib.import_module`, uma limitação descoberta e contornada no SOLAR.

### 2.3.1 Rastreamento de importações

**Rastreamento de importações** (_import tracing_) é uma forma específica de análise dinâmica: registrar cada módulo carregado, sua origem e a ordem. É útil para:

- confirmar se um módulo é realmente usado;
- detectar dependências dinâmicas;
- verificar a ordem de inicialização;
- comparar o que o grafo estático prevê com o que ocorre em execução.

No SOLAR, três cenários foram executados em processos separados: o verificador (`check`), o bootstrap da aplicação com SQLite temporário e a importação isolada do Model. Eles produziram 85, 172 e 13 módulos SOLAR, respectivamente, com uma união de 175.

---

## 2.4 Análise de dependências

**Análise de dependências** procura responder “quem usa quem”. Ela pode ser feita por AST, por rastreamento de runtime ou por ambas. O resultado é um conjunto de arestas:

```
nucleus.kernel → nucleus.database.database
nucleus.kernel → nucleus.storage.storage
nucleus.database.database → orbits.database.models.user_model
```

Cuidados indispensáveis:

- **não misturar** dependências internas com bibliotecas externas;
- **não misturar** código de produção com testes;
- definir se imports tardios contam (no SOLAR, contam, porque existem em runtime);
- definir como imports dinâmicos são tratados;
- registrar a resolução de imports relativos e de pacotes.

O SOLAR tem 306 arestas internas de produção; 234 comandos de importação externos (171 deles em produção) foram registrados separadamente e **não** entram em **Ca** — _afferent coupling_ (acoplamento aferente) (fan-in) — nem em **Ce** — _efferent coupling_ (acoplamento eferente) (fan-out).

---

## 2.5 Análise de grafos

Um **grafo** é um conjunto de **nós** (vértices) ligados por **arestas**. Em arquitetura:

- nó = módulo ou classe;
- aresta = dependência;
- direção = quem depende de quem;
- caminho = sequência de arestas;
- ciclo = caminho que volta ao nó inicial;
- **SCC** — _Strongly Connected Component_ (Componente Fortemente Conexo) = conjunto de nós em que todos alcançam todos.

A análise de grafos permite calcular fan-in, fan-out, instabilidade, ciclos e alcançabilidade. O SOLAR usou um algoritmo de Tarjan para SCCs e uma busca em largura (BFS) para alcançabilidade.

**Cuidado:** um grafo é tão bom quanto a regra que o construiu. Um grafo só com AST pode dizer “zero ciclos” e estar incompleto. Foi o que aconteceu antes do tracing: o ciclo `Database ↔ user_model` só apareceu quando a aresta dinâmica foi incluída.

---

## 2.6 Análise de métricas

**Métrica** é uma função que associa um elemento a um número (ou a uma categoria). Exemplos: CC de uma função, CBO de uma classe, fan-in de um módulo.

Uma métrica pode ser:

- **direta** — contagem simples (número de métodos);
- **derivada** — combinação de medidas (instabilidade, MI);
- **aproximada** — depende de uma representação parcial (CBO por AST, Halstead do Radon);
- **não aplicável** — a fórmula não tem domínio válido para o elemento (LCOM em classe sem atributos).

**Métrica não é teste.** Um teste verifica um comportamento esperado; uma métrica produz um número. Um teste pode passar enquanto a métrica indica risco; uma métrica pode indicar risco enquanto todos os testes passam.

---

## 2.7 Inspeção manual

Nem tudo é automatizável. A inspeção manual é necessária para:

- entender a intenção do código;
- distinguir um artefato de uma métrica de um problema real;
- verificar se um componente é de infraestrutura, composição ou domínio;
- interpretar um ciclo intencional;
- decidir se um módulo não carregado é API pública ou dívida.

No SOLAR, a inspeção manual foi usada para:

- confirmar que `Kernel.mount()` não instancia **CSRF** — _Cross-Site Request Forgery_ (Falsificação de Requisição entre Sites) —, rate limit, brute force e URL guard;
- verificar que `ControllerAndUseCaseMustUseNamedContracts` não está entre as 29 regras registradas;
- distinguir as responsabilidades de `DriverSQLAlchemy` e `ErrorLog` no LCOM4;
- confirmar que `nucleus.security.token` é importado por um teste (`tests/rules/test_controller_security_scanner.py`), mas não pela produção nem pelos cenários de runtime;

---

## 2.8 Testes automatizados

Testes automatizados verificam comportamentos. Eles são **evidência complementar** de qualidade, mas não substituem a análise estrutural. Um sistema com 100% de testes verdes pode ter:

- um ciclo de dependências;
- um módulo nunca carregado;
- uma classe com 15 responsabilidades;
- um acoplamento que impede reutilização.

No SOLAR, a suíte de testes existe e é usada como parte da saúde do projeto, mas **não** foi usada como prova de qualidade arquitetural. O foco desta documentação são as medições estruturais.

---

## 2.9 Validação independente

**Validar** é diferente de **reproduzir**. Reproduzir significa obter o mesmo número com o mesmo método. Validar significa verificar se o método mede o que se pretende e se o resultado resiste a uma checagem independente.

No SOLAR, a validação independente incluiu:

- recálculo de CC com a API do Radon, sem usar o JSON da **CLI** — _Command-Line Interface_ (Interface de Linha de Comando);
- recálculo de LCOM1/LCOM4 com implementação própria;
- recálculo de CBO das cinco classes de maior valor;
- recálculo de acoplamento de quatro módulos;
- recálculo de complexidade cognitiva com a mesma ferramenta;
- comparação de hashes entre execuções.

Resultados: CC, LCOM, CBO e cognitiva coincidiram exatamente; o acoplamento coincidiu em 3 de 4 módulos, e a diferença do quarto foi explicada por duas arestas dinâmicas.

---

## 2.10 Reprodutibilidade

Uma auditoria é **reprodutível** quando outra pessoa, com o mesmo código e as mesmas ferramentas, obtém os mesmos resultados. Para isso, é preciso registrar:

- versão do código (commit);
- versão de Python e das ferramentas;
- comandos exatos;
- escopo (produção × testes);
- exclusões;
- definição de cada métrica;
- forma de resolver imports;
- resultados e limitações.

O SOLAR tem scripts que geram todos os artefatos; após a correção de ordenação de empates, duas execuções produziram hashes idênticos.

---

## 2.11 Tabela comparativa das abordagens

| Abordagem                       | O que faz                               | O que consegue revelar                         | O que não consegue garantir                                   | Exemplo no SOLAR                                 |
| ------------------------------- | --------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------ |
| **Análise estática**            | lê a AST sem executar                   | imports, classes, métodos, atributos, decisões | imports dinâmicos, tipos resolvidos, comportamento em runtime | 306 arestas internas; ciclo estático ausente     |
| **Análise dinâmica**            | observa a execução                      | módulos carregados, ordem, causalidade         | cobertura de todos os cenários; caminhos não exercitados      | 175 módulos SOLAR observados em 3 cenários       |
| **Rastreamento de importações** | registra cada importação                | dependências reais, imports dinâmicos          | plugins/reflexão não instrumentados                           | `importlib(user_model)` no evento 684            |
| **Análise de dependências**     | constrói “quem usa quem”                | fan-in/fan-out, hubs, direção                  | intenção do projetista, qualidade da dependência              | `project_validator` com Ce 49                    |
| **Análise de grafos**           | calcula caminhos, ciclos, SCCs, alcance | ciclos, hubs, módulos inalcançáveis            | se um ciclo é intencional ou defeito                          | 1 SCC de tamanho 2; 207 SCCs no total            |
| **Métricas**                    | produz números                          | magnitude, distribuição, outliers              | qualidade real; interpretação contextual                      | CC máxima 10; MI saturado                        |
| **Inspeção manual**             | lê o código e o contexto                | intenção, responsabilidades, artefatos         | escala; reprodutibilidade plena                               | `Kernel.mount()` sem CSRF/rate limit             |
| **Testes automatizados**        | verifica comportamentos                 | corretude funcional                            | estrutura, acoplamento, evolução                              | suíte existente; não usada como prova estrutural |
| **Validação independente**      | recalcula com outro método              | erros de implementação, viés de ferramenta     | erro conceitual compartilhado                                 | LCOM1/LCOM4 com 0 divergências                   |
| **Reprodutibilidade**           | repete com registro                     | estabilidade do resultado                      | validade da interpretação                                     | hashes idênticos após correção                   |

---

## 2.12 O que uma auditoria **não** garante

- **Não garante ausência de defeitos funcionais.** Métricas não executam o sistema.
- **Não garante que o sistema seja fácil de manter.** Medem indicadores, não a experiência real.
- **Não garante cobertura total.** Cenários de runtime são finitos; análise estática tem pontos cegos.
- **Não substitui julgamento técnico.** Um número não decide se um ciclo é aceitável.
- **Não produz uma nota universal.** Contexto, domínio e objetivos mudam a interpretação.

---

## 2.13 Resumo do capítulo

- Auditoria é processo, não comando.
- Análise estática vê a estrutura; análise dinâmica vê o que acontece; nenhuma é completa sozinha.
- Métrica não é teste; teste não é análise estrutural.
- Validação independente e reprodutibilidade são partes do método, não luxo.
- Grafos dependem da regra de construção; “zero ciclos” pode ser um artefato de um grafo incompleto.

**Próximo capítulo:** como ler os números — média, mediana, percentil, distribuição, falsos positivos e causalidade.
