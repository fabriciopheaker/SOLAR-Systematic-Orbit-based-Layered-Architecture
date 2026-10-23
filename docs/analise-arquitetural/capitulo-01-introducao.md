# Capítulo 1 — Introdução à análise arquitetural

> **Pergunta deste capítulo:** o que é arquitetura de software, o que é analisá-la e por que um sistema pode funcionar corretamente e, ainda assim, ter problemas estruturais?

---

## 1.1 O que é arquitetura de software

Uma analogia: um prédio pode estar funcionando — as luzes acendem, os elevadores sobem, as torneiras abrem — e, mesmo assim, ter problemas estruturais: uma viga mal dimensionada, instalações elétricas que dificultam reformas, corredores que não conectam os ambientes. A **arquitetura** não é a decoração nem o funcionamento do dia a dia; é a **organização das partes, das ligações e das regras** que permitem que o prédio exista, seja mantido e possa ser modificado.

Em software, **arquitetura** é o conjunto de decisões sobre:

- quais **partes** existem (módulos, camadas, componentes);
- **como** essas partes se comunicam e dependem umas das outras;
- quais **regras** essas partes devem respeitar (por exemplo, quem pode acessar o banco, onde uma rota pode ser declarada);
- quais **responsabilidades** pertencem a cada parte;
- o que pode mudar sem afetar o restante.

A arquitetura de um sistema não é apenas a pasta onde os arquivos estão. Duas pastas iguais podem conter arquiteturas diferentes se as dependências e as responsabilidades forem diferentes. Também não é apenas um desenho: o desenho precisa corresponder ao que o código realmente faz.

### 1.1.1 A arquitetura SOLAR, em uma frase

A SOLAR — _Systematic Orbit-based Layered Architecture_ (Arquitetura Sistemática em Camadas Baseada em Órbitas) — organiza a aplicação em sete conceitos: **Nucleus** (governança), **Atmosphere** (mecanismos de execução), **Orbits** (trajetórias de acesso), **Planets** (módulos funcionais), **Environment** (configuração e recursos), **Observatory** (observabilidade) e **Satellites** (comunicação com outros módulos ou serviços externos).

Neste estudo de caso, a arquitetura é implementada em Python, com uma aplicação de exemplo pequena e um grande mecanismo de verificação das próprias regras arquiteturais. Essa assimetria é um resultado medido, não uma opinião: o subsistema `nucleus/rules` concentra 63,0% do SLOC de produção e 64,9% da complexidade ciclomática somada.

---

## 1.2 O que é análise arquitetural

**Análise arquitetural** é o processo de **produzir evidências** sobre a estrutura de um sistema para responder a perguntas como:

- As partes estão organizadas como o desenho diz?
- Existem dependências que não deveriam existir?
- Há partes que ninguém usa?
- Há caminhos circulares de dependência?
- A complexidade está concentrada em poucos pontos?
- O código é compreensível e modificável?
- As regras arquiteturais são verificáveis e efetivamente verificadas?

“Produzir evidências” é diferente de “dar uma opinião”. Uma evidência pode ser:

- um número calculado por uma ferramenta;
- um grafo de dependências;
- uma sequência de importações observada em execução;
- uma inspeção manual registrada;
- um teste automatizado.

A análise arquitetural **não** se limita a encontrar erros de execução. Um programa pode executar todas as funções corretamente e, ao mesmo tempo, ter um ciclo de dependências que dificulta testes, uma classe com responsabilidades demais ou um módulo que nunca é carregado.

### 1.2.1 Qualidade arquitetural

**Qualidade arquitetural** é o grau em que a estrutura do sistema favorece atributos desejados, como:

- **compreensibilidade** — é possível entender o sistema?
- **modificabilidade** — é possível mudar uma parte sem quebrar outras?
- **testabilidade** — é possível testar partes isoladamente?
- **confiabilidade estrutural** — as regras de dependência são respeitadas?
- **evolutividade** — é possível adicionar funcionalidades sem aumentar desproporcionalmente o custo?
- **segurança estrutural** — as decisões de segurança estão no lugar certo e não dependem de lembrança individual?

Esses atributos são chamados de **atributos de qualidade** (em inglês, _quality attributes_). Eles não são grandezas diretamente mensuráveis como massa ou temperatura. Medimos **indicadores** — números que se correlacionam com esses atributos em determinado contexto — e não a qualidade em si.

> **Cuidado:** um indicador não é a qualidade. Um **CC** — _Cyclomatic Complexity_ (Complexidade Ciclomática) — baixo não prova que o código é bom; um **CBO** — _Coupling Between Objects_ (Acoplamento entre Objetos) — alto não prova que o código é ruim. O indicador ajuda a formular perguntas melhores.

---

## 1.3 Componentes, módulos, classes, funções e métodos

Esses termos são frequentemente usados como sinônimos no dia a dia, mas medem coisas diferentes. A documentação usa definições operacionais claras:

| Termo          | Definição operacional                                                                                          | Exemplo no SOLAR                                               |
| -------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Componente** | parte arquitetural com responsabilidade definida; pode ser uma camada, um subsistema ou um conjunto de módulos | Nucleus, Orbits, Observatory                                   |
| **Módulo**     | arquivo Python importável (`.py`), identificado por um nome pontuado                                           | `nucleus.kernel`, `orbits.routes`, `observatory.log.error_log` |
| **Pacote**     | diretório Python com `__init__.py`; agrupa módulos                                                             | `nucleus.rules`, `orbits.planets.example`                      |
| **Classe**     | definição de um tipo de objeto, com atributos e métodos                                                        | `Database`, `Kernel`, `ErrorLog`                               |
| **Função**     | rotina definida no nível do módulo                                                                             | `main()` em `server.py`                                        |
| **Método**     | função definida dentro de uma classe                                                                           | `Kernel.mount()`, `Database.init()`                            |

**Por que a distinção importa:** o SOLAR tem 208 módulos de produção e 136 classes de produção. Dizer “o projeto tem 208 classes” seria errado; dizer “o projeto tem 208 módulos” também não é o mesmo que dizer “208 componentes”. Cada métrica usa uma unidade, e misturar unidades produz conclusões inválidas.

### 1.3.1 Dependências

Uma **dependência** existe quando uma parte precisa de outra para funcionar. Em Python, a forma mais comum é a **importação**:

```python
# nucleus/kernel.py (trecho)
from nucleus.database.database import Database
from nucleus.storage.storage import Storage
```

Nesse trecho, o módulo `nucleus.kernel` **depende** de `nucleus.database.database` e de `nucleus.storage.storage`.

Dependências também podem ser:

- **dinâmicas** — o nome do módulo é resolvido em tempo de execução, por exemplo com `importlib.import_module(...)`;
- **tardias** — a importação aparece dentro de uma função e só ocorre quando ela é chamada;
- **implícitas** — o Python carrega automaticamente o pacote-pai ao importar um submódulo (por exemplo, importar `observatory.log.error_log` carrega o pacote `observatory.log`).

A análise estática precisa de regras explícitas para cada caso. Ignorar dependências dinâmicas ou implícitas produz grafos incompletos — foi exatamente o que o tracing de runtime revelou no SOLAR.

---

## 1.4 Acoplamento

**Acoplamento** é o grau em que uma parte depende de outra. Há várias formas de medi-lo:

- quantos módulos dependem de um módulo (**fan-in**);
- de quantos módulos um módulo depende (**fan-out**);
- quantas classes uma classe referencia (**CBO**);
- se há caminhos circulares de dependência (**ciclos**).

Analogia: em uma cozinha, se todos os utensílios dependem de uma única tomada, a cozinha está **acoplada** àquela tomada. Trocar a tomada afeta tudo. Se cada bancada tem sua própria instalação, o acoplamento é menor — mas pode haver mais pontos para manter. O acoplamento não é “vilão” nem “herói”: ele é uma **escolha de projeto** com custos e benefícios.

### 1.4.1 Por que acoplamento importa

- **Impacto de mudança:** um módulo com fan-in alto é usado por muitos; mudar seu contrato pode afetar muitos pontos.
- **Testabilidade:** muitos dependentes dificultam isolar o módulo em testes.
- **Compreensão:** é preciso entender as dependências para entender o comportamento.
- **Riscos de inicialização:** dependências circulares podem exigir ordem de importação específica.

### 1.4.2 Um exemplo simples de sistema de cadastro

Imagine um sistema de cadastro com quatro partes:

```
Controlador → Serviço → Repositório → Banco de dados
```

- O **Controlador** recebe a requisição.
- O **Serviço** aplica regras de negócio.
- O **Repositório** lê e grava dados.
- O **Banco** armazena.

Se o Controlador importa diretamente o Repositório, o Serviço é ignorado e as regras ficam espalhadas. Se o Repositório importa o Controlador para “devolver a resposta”, há um ciclo. Se o Controlador importa o Banco diretamente, a camada de persistência perde sentido.

Nenhum desses problemas impede necessariamente o cadastro de funcionar no primeiro teste. Eles aparecem na manutenção, nos testes e na evolução.

### 1.4.3 O caso SOLAR

O SOLAR tem 306 dependências internas entre 208 módulos de produção. A direção predominante é **Planets → Nucleus** (11 arestas entre camadas), coerente com o desenho: os módulos funcionais usam os contratos e mecanismos do núcleo. Há, porém, 3 arestas de **Nucleus → Orbits**: uma importação tardia (`kernel → orbits.routes`) e duas dinâmicas (`database → models`). Isso não é automaticamente um defeito, mas é uma inversão que merece registro.

---

## 1.5 Coesão

**Coesão** é o grau em que as responsabilidades de uma parte estão relacionadas entre si. Uma classe coesa tem métodos que trabalham sobre o mesmo estado ou sobre o mesmo conceito. Uma classe pouco coesa junta coisas que não têm relação.

Analogia: uma caixa de ferramentas é coesa se contém ferramentas de marcenaria; é pouco coesa se mistura martelo, termômetro e chave de fenda. A caixa pode ser útil, mas não é uma unidade conceitual.

Coesão e acoplamento são dimensões diferentes:

- **coesão** olha para **dentro** da parte: as coisas ali dentro pertencem juntas?
- **acoplamento** olha para **fora**: a parte depende de quantas outras?

Uma classe pode ser coesa e muito acoplada (faz uma coisa só, mas depende de muitos módulos). Outra pode ser pouco coesa e pouco acoplada (faz várias coisas isoladas).

### 1.5.1 LCOM em uma frase

**LCOM** — _Lack of Cohesion of Methods_ (falta de coesão entre métodos) — tenta medir se os métodos de uma classe compartilham os mesmos atributos. Se cada método usa um conjunto diferente de dados, a classe pode estar acumulando responsabilidades distintas. No SOLAR, a métrica só é aplicável a 39 das 136 classes; nas demais, a fórmula não tem domínio válido (por exemplo, classes sem atributos de instância). Voltaremos a isso no Capítulo 5B.

---

## 1.6 Complexidade

**Complexidade de software** é o grau de dificuldade para entender, testar e modificar o código. Ela tem várias facetas:

- **complexidade de controle** — quantos caminhos o fluxo pode seguir (CC);
- **complexidade cognitiva** — quanto esforço de leitura o fluxo exige;
- **complexidade de expressão** — quantos operadores e operandos aparecem (Halstead);
- **complexidade estrutural** — tamanho e emaranhamento de dependências.

Nenhuma dessas facetas, isolada, representa “a complexidade do sistema”. Uma função com CC 2 pode ser difícil de ler se tiver nomes ruins; um sistema com CC baixa pode ter uma arquitetura emaranhada.

### 1.6.1 Complexidade não é o mesmo que qualidade

Uma função complexa pode ser inevitável (um analisador sintático, por exemplo) e estar correta. Uma função simples pode estar no lugar errado da arquitetura. A pergunta útil é: **a complexidade está onde deveria estar?** No SOLAR, a maior parte da complexidade está no próprio mecanismo de governança, não nos módulos funcionais. Isso pode ser adequado para uma arquitetura de referência, mas precisa ser dito com clareza.

---

## 1.7 Manutenibilidade

**Manutenibilidade** é a facilidade com que um sistema pode ser corrigido, adaptado e evoluído. Ela depende de:

- legibilidade;
- coesão e acoplamento;
- complexidade;
- documentação;
- testes;
- clareza das fronteiras arquiteturais.

O **MI** — _Maintainability Index_ (Índice de Manutenibilidade) — é uma tentativa de resumir isso em um número. No SOLAR, o MI foi reproduzido com fidelidade ao Radon, mas **não discrimina**: 100% dos módulos ficam em rank A e 110 dos 208 módulos de produção recebem exatamente 100 porque o volume Halstead é zero. Isso será detalhado no Capítulo 5C.

### 1.7.1 Evolutividade

**Evolutividade** é a capacidade de adicionar ou alterar funcionalidades com custo proporcional. Uma arquitetura evolutiva tem fronteiras claras, dependências controladas e pontos de extensão previsíveis. Um exemplo no SOLAR: um Planet novo é registrado em `orbits/routes.py` e segue o contrato dos demais; não é necessário alterar o `Kernel`. Já o registro de regras é manual em `ProjectValidator`: cada nova regra exige edição do validador. Isso não é um defeito, mas é uma característica com custo de evolução.

---

## 1.8 Por que um sistema pode funcionar e ainda ter problemas estruturais

Três exemplos reais do SOLAR ajudam a entender:

1. **O sistema passa na verificação arquitetural, mas há um ciclo dinâmico.** O validador do SOLAR reportou 0 violações no código atual. Ainda assim, `nucleus.database.database` importa dinamicamente `orbits.database.models.user_model`, que importa `nucleus.database.database` no topo. O ciclo não é visível para uma análise puramente sintática.
2. **Um módulo pode não ser carregado em nenhum cenário e ainda não ser “código morto”.** Catorze módulos de produção não foram carregados nos cenários de runtime, incluindo todo o subsistema de upload e seis módulos de segurança de borda. Eles podem ser **API** — _Application Programming Interface_ (Interface de Programação de Aplicações) — pública, código preparado ou integração pendente; a ausência de importação não prova desuso.
3. **Um alerta de ferramenta pode estar errado.** O relatório estrutural original acusou “baixa coesão” em `Database`, `Storage` e `DatabaseDriver`. As três classes não têm atributos de instância: a fórmula do LCOM, aplicada a elas, produz `C(n,2)` por construção. O alerta é um **falso positivo**, não um problema de projeto.

**Conclusão:** funcionar é necessário, mas não suficiente. A análise arquitetural investiga a estrutura que sustenta o funcionamento e a evolução.

---

## 1.9 Defeito funcional, risco arquitetural, problema de manutenção e limitação de métrica

Esses quatro conceitos são frequentemente confundidos. A tabela abaixo fixa a diferença:

| Conceito                   | O que é                                                                       | Exemplo                                                           | Como se confirma                                |
| -------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| **Defeito funcional**      | o sistema faz algo errado em relação ao esperado                              | uma rota devolve 500 quando deveria devolver 400                  | teste funcional, reprodução do erro             |
| **Risco arquitetural**     | uma característica estrutural que pode dificultar evolução, teste ou operação | ciclo `Database ↔ user_model`; 14 módulos fora do fluxo observado | análise de dependências, tracing, inspeção      |
| **Problema de manutenção** | o código é difícil de entender ou alterar                                     | função de 163 linhas; classe com três responsabilidades distintas | leitura, métricas, revisão                      |
| **Limitação de métrica**   | a métrica não mede o que se pretende, ou não se aplica ao caso                | Halstead com 52,62% de funções zeradas; LCOM em classe sem estado | validação metodológica, comparação independente |

**Regra prática:** antes de dizer “há um problema”, pergunte **qual é a evidência** e **qual é o conceito** que ela sustenta. Um número alto pode ser um risco, um artefato ou uma característica intencional.

---

## 1.10 O que este capítulo fixou

- Arquitetura é a organização das partes, dependências, responsabilidades e regras — não apenas pastas ou desenhos.
- Análise arquitetural produz evidências; não é sinônimo de teste funcional.
- Qualidade arquitetural é multidimensional e não se reduz a um número.
- Módulo, classe, função e método são unidades diferentes.
- Acoplamento olha para fora; coesão olha para dentro.
- Complexidade tem várias facetas; nenhuma isolada representa o sistema.
- Um sistema pode funcionar e ter riscos estruturais; um alerta pode ser falso positivo; uma métrica pode não se aplicar.

**Próximo capítulo:** como uma auditoria arquitetural é executada, quais abordagens existem e o que cada uma consegue (e não consegue) garantir.
