# Capítulo 6 — Glossário

> **Como usar:** termos em português vêm primeiro; a forma original em inglês aparece entre parênteses. As siglas estão expandidas na primeira coluna.

---

## 6.1 Termos de arquitetura e método

| Termo                      | Expansão / origem                                                                                     | Definição                                                                                                                  | Onde aparece   |
| -------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------- |
| **SOLAR**                  | _Systematic Orbit-based Layered Architecture_ (Arquitetura em Camadas Sistemática Baseada em Órbitas) | Estilo arquitetural do projeto: núcleo, atmosfera, órbitas, planetas, ambiente, observatório e satélites.                  | Capítulos 1, 8 |
| **Nucleus**                | Núcleo                                                                                                | Camada de regras, contratos, segurança, persistência e infraestrutura conceitual.                                          | 1, 8           |
| **Atmosphere**             | Atmosfera                                                                                             | Camada de middleware e tratamento de requisições.                                                                          | 1, 8           |
| **Orbits**                 | Órbitas                                                                                               | Camada de composição e persistência concreta.                                                                              | 1, 8           |
| **Planets**                | Planetas                                                                                              | Módulos funcionais (ex.: usuário).                                                                                         | 1, 8           |
| **Environment**            | Ambiente                                                                                              | Configuração e variáveis de ambiente.                                                                                      | 1, 8           |
| **Observatory**            | Observatório                                                                                          | Ferramentas de verificação e relatórios.                                                                                   | 1, 8           |
| **Satellites**             | Satélites                                                                                             | Integrações externas.                                                                                                      | 1, 8           |
| **Bootstrap**              | Inicialização                                                                                         | Camada que monta a aplicação (`Kernel`).                                                                                   | 1, 8           |
| **composition root**       | Raiz de composição                                                                                    | Ponto único onde as dependências são instanciadas e ligadas.                                                               | 5A, 5C         |
| **módulo**                 | —                                                                                                     | Arquivo Python importável.                                                                                                 | 1–5            |
| **pacote**                 | —                                                                                                     | Diretório Python com `__init__.py`.                                                                                        | 1, 5B          |
| **classe**                 | —                                                                                                     | Definição de tipo com atributos e métodos.                                                                                 | 1–5            |
| **função**                 | —                                                                                                     | Bloco nomeado de código; pode ser método.                                                                                  | 1–5            |
| **método**                 | —                                                                                                     | Função definida dentro de uma classe.                                                                                      | 1–5            |
| **dependência**            | —                                                                                                     | Relação em que um elemento precisa de outro para funcionar.                                                                | 1–5            |
| **grafo de dependências**  | _dependency graph_                                                                                    | Nós = módulos; arestas = imports.                                                                                          | 5A             |
| **aresta**                 | _edge_                                                                                                | Ligação entre dois nós do grafo.                                                                                           | 5A             |
| **nó**                     | _node_                                                                                                | Elemento do grafo (módulo, classe, função).                                                                                | 5A             |
| **caminho**                | _path_                                                                                                | Sequência de arestas entre nós.                                                                                            | 5A             |
| **ciclo**                  | _cycle_                                                                                               | Caminho que volta ao nó de origem.                                                                                         | 5A             |
| **SCC**                    | _Strongly Connected Component_ (Componente Fortemente Conexo)                                         | Conjunto de nós em que todos se alcançam mutuamente.                                                                       | 5A             |
| **BFS**                    | _Breadth-First Search_ (Busca em Largura)                                                             | Percurso que explora vizinhos por níveis.                                                                                  | 5B             |
| **DFS**                    | _Depth-First Search_ (Busca em Profundidade)                                                          | Percurso que vai o mais fundo possível antes de voltar.                                                                    | 5A             |
| **Tarjan**                 | Algoritmo de Tarjan                                                                                   | Algoritmo para encontrar SCCs em tempo linear.                                                                             | 5A             |
| **alcançabilidade**        | _reachability_                                                                                        | Propriedade de um nó ser alcançável a partir de um ponto de entrada.                                                       | 5B             |
| **ponto de entrada**       | _entry point_                                                                                         | Módulo por onde a execução começa (`server`, `__main__`).                                                                  | 5B             |
| **código morto**           | _dead code_                                                                                           | Código que nunca pode ser executado. **Não é o mesmo que “não observado”.**                                                | 5B             |
| **hub**                    | —                                                                                                     | Nó com muitas conexões.                                                                                                    | 5A             |
| **fan-in**                 | _fan-in_ / _afferent coupling_                                                                        | Número de módulos que dependem do módulo analisado (**Ca**).                                                               | 5A             |
| **fan-out**                | _fan-out_ / _efferent coupling_                                                                       | Número de módulos dos quais o módulo analisado depende (**Ce**).                                                           | 5A             |
| **acoplamento**            | _coupling_                                                                                            | Grau de dependência entre elementos.                                                                                       | 1, 5A          |
| **coesão**                 | _cohesion_                                                                                            | Grau em que elementos de um módulo/classe pertencem juntos.                                                                | 1, 5B          |
| **instabilidade**          | _instability_                                                                                         | `I = Ce / (Ca + Ce)`.                                                                                                      | 5A             |
| **I**                      | _Instability_ (Instabilidade)                                                                         | Sigla de instabilidade; razão entre fan-out e a soma de fan-in e fan-out.                                                  | 5A             |
| **abstração**              | _abstractness_                                                                                        | Proporção de abstrações em um módulo (não medida neste projeto).                                                           | 5A             |
| **linha de base**          | _baseline_                                                                                            | Medição de referência do próprio projeto.                                                                                  | 3              |
| **limite de referência**   | _threshold_                                                                                           | Valor externo usado como comparação.                                                                                       | 3              |
| **falso positivo**         | _false positive_                                                                                      | Alerta para problema inexistente.                                                                                          | 3              |
| **falso negativo**         | _false negative_                                                                                      | Problema existente não detectado.                                                                                          | 3              |
| **aproximação**            | _approximation_                                                                                       | Medida obtida com representação parcial.                                                                                   | 3, 5A          |
| **validação independente** | _independent validation_                                                                              | Recálculo por outro método/implementação.                                                                                  | 2, 3           |
| **reprodutibilidade**      | _reproducibility_                                                                                     | Mesmo método + mesmo código = mesmos resultados.                                                                           | 5D             |
| **determinismo**           | _determinism_                                                                                         | Ausência de variação não explicada entre execuções.                                                                        | 5D             |
| **tracing**                | _tracing_                                                                                             | Registro de eventos em tempo de execução.                                                                                  | 5D             |
| **audit hook**             | _audit hook_                                                                                          | Gancho do Python (`sys.addaudithook`) que observa eventos.                                                                 | 5D             |
| **instrumentação**         | _instrumentation_                                                                                     | Inserir código para observar comportamento.                                                                                | 5D             |
| **cenário**                | _scenario_                                                                                            | Execução controlada para observar um fluxo.                                                                                | 5D             |
| **CBO**                    | _Coupling Between Objects_ (Acoplamento entre Objetos)                                                | Número de classes distintas referenciadas por uma classe.                                                                  | 5A             |
| **NOM**                    | _Number of Methods_ (Número de Métodos)                                                               | Quantidade de métodos de uma classe.                                                                                       | 5D             |
| **NOC**                    | _Number of Classes_ (Número de Classes)                                                               | Quantidade de classes em um escopo.                                                                                        | 5D             |
| **WMC**                    | _Weighted Methods per Class_ (Métodos Ponderados por Classe)                                          | Soma de complexidades dos métodos; não usada neste projeto.                                                                | 2              |
| **LCOM**                   | _Lack of Cohesion of Methods_ (Falta de Coesão dos Métodos)                                           | Família de métricas de coesão.                                                                                             | 5B             |
| **LCOM1**                  | _LCOM_ variante 1                                                                                     | `max(0, P − Q)`, pares de métodos sem/com atributo compartilhado.                                                          | 5B             |
| **LCOM4**                  | _LCOM_ variante 4                                                                                     | Número de componentes conexos de métodos.                                                                                  | 5B             |
| **LCOM\***                 | _LCOM star_                                                                                           | Coesão normalizada de Henderson-Sellers.                                                                                   | 5B             |
| **TCC**                    | _Tight Class Cohesion_ (Coesão Estreita de Classe)                                                    | Proporção de pares de métodos diretamente conectados.                                                                      | 5B             |
| **CC**                     | _Cyclomatic Complexity_ (Complexidade Ciclomática)                                                    | Número de caminhos independentes.                                                                                          | 5C             |
| **complexidade cognitiva** | _Cognitive Complexity_                                                                                | Esforço de leitura, com penalidade de aninhamento.                                                                         | 5C             |
| **CFG**                    | _Control Flow Graph_ (Grafo de Fluxo de Controle)                                                     | Grafo de nós e arestas de execução de uma função.                                                                          | 5C             |
| **Halstead**               | Métricas de Halstead                                                                                  | Volume, dificuldade e esforço a partir de operadores/operandos.                                                            | 5C             |
| **MI**                     | _Maintainability Index_ (Índice de Manutenibilidade)                                                  | Métrica composta de 0 a 100.                                                                                               | 5C             |
| **LOC**                    | _Lines of Code_ (Linhas de Código)                                                                    | Linhas físicas.                                                                                                            | 5C             |
| **SLOC**                   | _Source Lines of Code_ (Linhas de Código-Fonte)                                                       | Linhas com código, sem branco/comentário.                                                                                  | 5C             |
| **LLOC**                   | _Logical Lines of Code_ (Linhas Lógicas de Código)                                                    | Instruções lógicas.                                                                                                        | 5C             |
| **P90**                    | 90º percentil                                                                                         | Valor abaixo do qual ficam 90% dos dados.                                                                                  | 3              |
| **rank A–F**               | —                                                                                                     | Faixas de classificação do Radon para CC.                                                                                  | 5C             |
| **ABC/Protocol**           | `abc.ABC`, `typing.Protocol`                                                                          | Classes-base abstratas e protocolos estruturais do Python.                                                                 | 5D             |
| **ORM**                    | _Object-Relational Mapping_ (Mapeamento Objeto-Relacional)                                            | Camada que mapeia classes para tabelas.                                                                                    | 1, 5A          |
| **SQL**                    | _Structured Query Language_ (Linguagem de Consulta Estruturada)                                       | Linguagem de consulta a bancos relacionais.                                                                                | 5A             |
| **DB**                     | _Database_ (Banco de Dados)                                                                           | Sistema de persistência.                                                                                                   | 5A             |
| **API**                    | _Application Programming Interface_ (Interface de Programação de Aplicações)                          | Conjunto de contratos públicos de um sistema.                                                                              | 1, 5B          |
| **CLI**                    | _Command-Line Interface_ (Interface de Linha de Comando)                                              | Interface por comandos de terminal.                                                                                        | 2              |
| **AST**                    | _Abstract Syntax Tree_ (Árvore de Sintaxe Abstrata)                                                   | Representação estruturada do código produzida pelo parser.                                                                 | 2, 5A          |
| **JSON**                   | _JavaScript Object Notation_ (Notação de Objetos JavaScript)                                          | Formato de dados textuais.                                                                                                 | 2, 5C          |
| **CSV**                    | _Comma-Separated Values_ (Valores Separados por Vírgula)                                              | Formato tabular simples.                                                                                                   | 2              |
| **HTTP**                   | _Hypertext Transfer Protocol_ (Protocolo de Transferência de Hipertexto)                              | Protocolo de comunicação web.                                                                                              | 1, 5D          |
| **HTTPS**                  | _HTTP Secure_ (HTTP Seguro)                                                                           | HTTP sobre TLS.                                                                                                            | 1              |
| **URL**                    | _Uniform Resource Locator_ (Localizador Uniforme de Recursos)                                         | Endereço de recurso na web.                                                                                                | 5A             |
| **CORS**                   | _Cross-Origin Resource Sharing_ (Compartilhamento de Recursos entre Origens)                          | Política de acesso entre origens.                                                                                          | 5D             |
| **CSRF**                   | _Cross-Site Request Forgery_ (Falsificação de Requisição entre Sites)                                 | Ataque que força requisições autenticadas.                                                                                 | 5B             |
| **JWT**                    | _JSON Web Token_ (Token Web JSON)                                                                     | Token assinado com claims.                                                                                                 | 1              |
| **UUID**                   | _Universally Unique Identifier_ (Identificador Único Universal)                                       | Identificador de 128 bits.                                                                                                 | 5B             |
| **UTF-8**                  | _Unicode Transformation Format – 8 bits_                                                              | Codificação de caracteres Unicode.                                                                                         | 2              |
| **DLL**                    | _Dynamic-Link Library_ (Biblioteca de Vínculo Dinâmico)                                               | Biblioteca carregada em tempo de execução no Windows.                                                                      | 2              |
| **PyPI**                   | _Python Package Index_ (Índice de Pacotes Python)                                                     | Repositório oficial de pacotes Python.                                                                                     | 7              |
| **Radon**                  | —                                                                                                     | Ferramenta Python de métricas (CC, Halstead, MI, raw).                                                                     | 7              |
| **flake8**                 | —                                                                                                     | Ferramenta de lint que agrega plugins.                                                                                     | 7              |
| **SonarQube**              | —                                                                                                     | Plataforma de análise de qualidade.                                                                                        | 7              |
| **S3776**                  | Regra Sonar                                                                                           | Regra de complexidade cognitiva com limiar padrão 15.                                                                      | 5C             |
| **CVE**                    | _Common Vulnerabilities and Exposures_ (Vulnerabilidades e Exposições Comuns)                         | Identificador público de vulnerabilidade.                                                                                  | 2              |
| **FP**                     | _False Positive_ (Falso Positivo)                                                                     | Alerta incorreto.                                                                                                          | 3              |
| **FN**                     | _False Negative_ (Falso Negativo)                                                                     | Problema não detectado.                                                                                                    | 3              |
| **ADR**                    | _Architecture Decision Record_ (Registro de Decisão Arquitetural)                                     | Documento que registra uma decisão.                                                                                        | 1              |
| **ROF**                    | _Restrições de Organização Estrutural e Fluxo HTTP_                                                   | Categoria de regras do SOLAR que define organização de componentes, estrutura de módulos e fluxo de requisições/respostas. | 5D             |
| **SEG-008**                | Regra de segurança do projeto                                                                         | Regra que proíbe expor detalhes internos em mensagens de erro.                                                             | 2, 5D          |
| **N/A**                    | _Not Applicable_ (Não Aplicável)                                                                      | Resultado em que a métrica não tem domínio válido.                                                                         | 5B, 5C         |

---

## 6.2 Termos estatísticos

| Termo             | Definição                                                  |
| ----------------- | ---------------------------------------------------------- |
| **média**         | Soma dividida pela quantidade.                             |
| **mediana**       | Valor central da amostra ordenada.                         |
| **percentil**     | Valor abaixo do qual uma proporção dos dados fica.         |
| **distribuição**  | Forma como os valores se espalham.                         |
| **contagem**      | Número absoluto de ocorrências.                            |
| **proporção**     | Contagem dividida pelo total.                              |
| **amostra**       | Subconjunto de elementos medidos.                          |
| **população**     | Conjunto completo de elementos.                            |
| **outlier**       | Valor muito distante do padrão.                            |
| **tendência**     | Direção de mudança ao longo do tempo.                      |
| **correlação**    | Variação conjunta entre duas medidas.                      |
| **causalidade**   | Relação em que uma medida provoca a outra.                 |
| **sensibilidade** | Quanto um resultado muda quando o método muda.             |
| **saturação**     | Situação em que muitos casos atingem o mesmo valor limite. |
| **denominador**   | Total usado como base de uma proporção.                    |

---

## 6.3 Termos do SOLAR

| Termo                    | Definição                                                                              |
| ------------------------ | -------------------------------------------------------------------------------------- |
| **regra arquitetural**   | Restrição que o código deve respeitar (ex.: controllers não implementam autenticação). |
| **scanner**              | Componente que varre a AST em busca de um padrão.                                      |
| **violação**             | Ocorrência em que uma regra é desrespeitada.                                           |
| **conformidade**         | Ausência de violações para as regras executadas.                                       |
| **regra não registrada** | Regra implementada que não está instanciada no validador.                              |
| **planeta**              | Módulo funcional na camada Planets.                                                    |
| **satélite**             | Integração externa.                                                                    |
| **ambiente**             | Configuração externalizada.                                                            |
| **observatório**         | Ferramentas de verificação.                                                            |

---

## 6.4 Observações finais

- **Siglas não são universais.** `NOC` pode significar _Number of Children_ em outras obras; aqui significa _Number of Classes_, conforme o relatório do projeto.
- **`ROF`** significa _Restrições de Organização Estrutural e Fluxo HTTP_, conforme `docs/rules.md`.
- **Termos em inglês** são mantidos quando são nomes próprios de ferramentas, regras ou métricas consagradas.

**Próximo:** [Capítulo 7](capitulo-07-ferramentas.md) — ferramentas usadas e seus limites.
