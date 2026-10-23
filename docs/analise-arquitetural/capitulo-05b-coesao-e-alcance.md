# Capítulo 5B — Catálogo: coesão e alcançabilidade

> Continuação do catálogo iniciado no [Capítulo 5A](capitulo-05a-acoplamento-e-ciclos.md).

---

## 5.10 Coesão: LCOM1, LCOM4, LCOM\* e TCC

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                                                                                                                                                                               |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Nome em português                   | Falta de coesão dos métodos; componentes conexos; coesão normalizada; coesão tight class                                                                                                                                                                                                                                                                                               |
| 2   | Nome original                       | _Lack of Cohesion of Methods_; _LCOM1_; _LCOM4_; \*LCOM\**; *Tight Class Cohesion\*                                                                                                                                                                                                                                                                                                    |
| 3   | Sigla                               | **LCOM** (_Lack of Cohesion of Methods_), **TCC** (_Tight Class Cohesion_)                                                                                                                                                                                                                                                                                                             |
| 4   | Categoria                           | coesão                                                                                                                                                                                                                                                                                                                                                                                 |
| 5   | O que é, em linguagem simples       | Mede se os métodos de uma classe usam o mesmo “estado” (atributos). Se cada método usa um conjunto diferente de atributos, a classe parece fazer várias coisas.                                                                                                                                                                                                                        |
| 6   | O que mede exatamente               | **LCOM1:** `max(0, P − Q)`, em que P = pares de métodos que não compartilham atributos e Q = pares que compartilham. **LCOM4:** número de componentes conexos de métodos, ligados por atributo compartilhado ou chamada. **LCOM\*:** `(média de atributos por método − m) / (1 − m)`, com m métodos. **TCC:** pares diretamente conectados ÷ total de pares.                           |
| 7   | Por que é importante                | Ajuda a detectar classes que acumulam responsabilidades e classes que são apenas agrupamentos de funções.                                                                                                                                                                                                                                                                              |
| 8   | Como é calculado                    | Para cada classe: lista de métodos de instância (excluindo `__init__` na variante principal), atributos usados por cada método e chamadas entre métodos. P, Q, componentes e proporções derivam dessas listas.                                                                                                                                                                         |
| 9   | Como interpretar                    | **LCOM1** alto: pouca sobreposição de atributos. **LCOM4** = 1: todos os métodos estão conectados; >1: grupos independentes. **TCC** alto: métodos compartilham atributos. **LCOM\*** alto: métodos usam poucos atributos. Sempre com o contexto da classe.                                                                                                                            |
| 10  | Cenário favorável                   | `LCOM4 = 1` e TCC razoável: métodos formam um conjunto conectado.                                                                                                                                                                                                                                                                                                                      |
| 11  | Cenário potencialmente desfavorável | `LCOM4 > 1` em classe de domínio com atributos: indício de múltiplas responsabilidades.                                                                                                                                                                                                                                                                                                |
| 12  | Exemplo numérico                    | Classe com métodos m1 (usa `a`), m2 (usa `a,b`), m3 (usa `b`): pares m1-m2 e m2-m3 compartilham; m1-m3 não. LCOM1 = max(0, 1−2) = 0. LCOM4 = 1. TCC = 2/3 = 0,667. LCOM\* = (1,333−3)/(1−3) = 0,833.                                                                                                                                                                                   |
| 13  | Exemplo no SOLAR                    | 39 classes têm LCOM aplicável (28,7% de 136). LCOM1: mediana 3, média 10,82, P90 28, máximo 89 (`ErrorExposureScanner`, 14 métodos e 1 atributo). LCOM4: média 1,13, máximo 3. TCC: mediana 0,30, média 0,398. LCOM\*: mediana 0,75, média 0,651, máximo 1,0. Quatro classes têm LCOM4 > 1: `DriverSQLAlchemy` (3), `Kernel` (2), `SecretsMustNotAppearInSource` (2) e `ErrorLog` (2). |
| 14  | Limitações                          | Só considera atributos de instância; estado de classe, atributos de módulo e serviços injetados não entram; LCOM1 cresce com o número de métodos por construção; LCOM4 conta conexão por chamada, que pode mascarar baixa coesão de estado; classes sem atributos de instância não têm domínio válido.                                                                                 |
| 15  | Erros comuns                        | Aplicar LCOM a classes sem atributos (resultado `C(n,2)` por construção); tratar LCOM1 alto como prova de baixa coesão; ignorar que 97 classes são N/A; comparar LCOM entre classes de tamanhos diferentes.                                                                                                                                                                            |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py`; validação independente V5 (LCOM exato nas 39 classes aplicáveis).                                                                                                                                                                                                                                                                                                  |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (fórmulas conferidas; interpretação depende de aplicabilidade).                                                                                                                                                                                                                                                                                             |
| 18  | O que se pode/não se pode concluir  | Pode-se identificar classes candidatas a revisão e medir conectividade de métodos. Não se pode concluir que a classe “faz coisas demais” sem ler o código; nem aplicar LCOM a classes sem estado de instância.                                                                                                                                                                         |

### 5.10.1 Por que 97 classes são N/A

| Motivo                          | Quantidade | Exemplos                                                       |
| ------------------------------- | ---------- | -------------------------------------------------------------- |
| Menos de 2 métodos de instância | 54         | classes com um único método ou apenas `__init__`               |
| Sem atributos de instância      | 42         | `Database`, `Storage`, `DatabaseDriver`, regras de arquitetura |
| Nenhum método usa o estado      | 1          | classe com estado declarado, mas sem uso                       |
| **Total N/A**                   | **97**     |                                                                |

Aplicar LCOM1 a `Database` produz 15 porque há 6 métodos e nenhum atributo compartilhado: `C(6,2) = 15`. O número é matematicamente correto e arquiteturalmente **sem sentido**. O mesmo vale para `Storage` (15) e `DatabaseDriver` (21).

### 5.10.2 Quatro classes com LCOM4 > 1

| Classe                         | LCOM4 | LCOM1 | Métodos | Atributos | Leitura                                                                                                                 |
| ------------------------------ | ----- | ----- | ------- | --------- | ----------------------------------------------------------------------------------------------------------------------- |
| `DriverSQLAlchemy`             | 3     | 12    | 9       | 3         | três grupos de métodos: conexão/execução, transação, inspeção. **Merece investigação.**                                 |
| `Kernel`                       | 2     | 1     | 3       | 10        | `mount()` e os demais métodos formam grupos separados; é um composition root, mas o acoplamento interno merece leitura. |
| `SecretsMustNotAppearInSource` | 2     | 10    | 5       | 3         | regra com grupos de varredura distintos; verificar se a separação é intencional.                                        |
| `ErrorLog`                     | 2     | 1     | 7       | 5         | dois grupos de métodos; pode refletir dois usos do log (registro e consulta).                                           |

**Nenhum desses casos é, por si, um defeito.** São candidatos a inspeção manual, com custo e contexto.

### 5.10.3 O caso `ErrorExposureScanner`

- 14 métodos, 1 atributo → LCOM1 = 89 (de 91 pares possíveis).
- LCOM4 = 1: todos os métodos se conectam por chamadas.
- Leitura: os métodos compartilham pouco **estado**, mas formam um fluxo de varredura conectado. LCOM1 alto aqui não significa “classe ruim”; significa “classe funcional com estado mínimo”.
- **Lição:** LCOM1 e LCOM4 podem discordar; a discordância é informação, não erro.

### 5.10.4 LCOM × coesão percebida

Coesão percebida por quem lê o código envolve nomes, contrato, responsabilidade e domínio. LCOM mede apenas compartilhamento de estado. Uma classe pode ter LCOM baixo e ser conceitualmente incoerente; outra pode ter LCOM alto e ser perfeitamente coesa em termos de fluxo. A métrica é um **indício**, não um veredito.

---

## 5.12 Alcançabilidade

| #   | Campo                               | Conteúdo                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Nome em português                   | Alcançabilidade; módulos alcançáveis e não alcançáveis                                                                                                                                                                                                                                                                                                                                                                                     |
| 2   | Nome original                       | _Reachability_; _unreachable modules_                                                                                                                                                                                                                                                                                                                                                                                                      |
| 3   | Sigla                               | não há sigla consagrada; no projeto usa-se **BFS** para o percurso                                                                                                                                                                                                                                                                                                                                                                         |
| 4   | Categoria                           | alcance e utilização                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 5   | O que é, em linguagem simples       | Partindo dos pontos de entrada, quais módulos podem ser carregados seguindo as dependências?                                                                                                                                                                                                                                                                                                                                               |
| 6   | O que mede exatamente               | Conjunto de módulos de produção alcançáveis por busca em largura (BFS) no grafo de imports, a partir de `server` e `observatory.solar.__main__`, incluindo dois alvos dinâmicos modelados (`orbits.database.models` e `user_model`).                                                                                                                                                                                                       |
| 7   | Por que é importante                | Módulos não alcançáveis são candidatos a código não utilizado ou a funcionalidade não conectada; módulos alcançáveis mas nunca observados em execução indicam cenários não cobertos.                                                                                                                                                                                                                                                       |
| 8   | Como é calculado                    | BFS sobre arestas internas; comparação com o conjunto de módulos vistos em runtime via `sys.modules` e auditoria de importações.                                                                                                                                                                                                                                                                                                           |
| 9   | Como interpretar                    | Não alcançável: candidato a inspeção. Alcançável e observado: fluxo coberto. Alcançável e não observado: cenário não exercitado.                                                                                                                                                                                                                                                                                                           |
| 10  | Cenário favorável                   | Todo módulo com código é alcançável a partir de um ponto de entrada declarado.                                                                                                                                                                                                                                                                                                                                                             |
| 11  | Cenário potencialmente desfavorável | Módulos de segurança ou de regra não alcançáveis e não registrados: funcionalidade possivelmente incompleta.                                                                                                                                                                                                                                                                                                                               |
| 12  | Exemplo numérico                    | Grafo com arestas `server → kernel`, `kernel → database`, `kernel → routes`; a partir de `server`, BFS alcança kernel, database e routes. Um módulo `token` sem aresta de entrada não é alcançado.                                                                                                                                                                                                                                         |
| 13  | Exemplo no SOLAR                    | **Estático:** 134 de 208 módulos alcançáveis; 74 não alcançáveis, dos quais 59 são inicializadores sem código e 15 têm código (631 SLOC). **Runtime (3 cenários):** união de 175 módulos SOLAR observados, 133 com código e 42 inicializadores implícitos; 14 dos 15 candidatos não apareceram em nenhum cenário (625 SLOC, 9,98% do SLOC de produção). `observatory.records` foi observado e, portanto, **refutado** como não alcançável. |
| 14  | Limitações                          | Depende dos pontos de entrada declarados; imports dinâmicos não instrumentados podem criar arestas invisíveis; três cenários não cobrem todos os fluxos (rotas, middlewares, tarefas); ausência em runtime não prova ausência de uso; pacotes-pai são carregados implicitamente e não aparecem no grafo estático.                                                                                                                          |
| 15  | Erros comuns                        | Chamar módulo não alcançável de “código morto”; ignorar que 59 inicializadores não têm código; comparar 15 (estático) com 14 (runtime) sem explicar a diferença; concluir que a API é inútil por não ter sido exercitada.                                                                                                                                                                                                                  |
| 16  | Ferramenta/procedimento no SOLAR    | `solar_metrics.py` (BFS) + `trace_imports.py` (runtime); `alcancabilidade.json`, `comparacao_alcancabilidade.json`.                                                                                                                                                                                                                                                                                                                        |
| 17  | Status                              | **VALIDADO COM RESSALVAS** (estático reproduzível; runtime cobre 3 cenários, não todos os fluxos).                                                                                                                                                                                                                                                                                                                                         |
| 18  | O que se pode/não se pode concluir  | Pode-se afirmar que 14 módulos não foram carregados em nenhum dos cenários e medir seu tamanho. Não se pode afirmar que são inúteis, mortos ou sem efeito; nem que todo o restante está coberto.                                                                                                                                                                                                                                           |

### 5.12.1 Os 14 módulos ausentes em runtime

| Módulo                                                                       | SLOC | Observação                     |
| ---------------------------------------------------------------------------- | ---- | ------------------------------ |
| `nucleus.contracts.responsibility_contract`                                  | 6    | contrato de responsabilidade   |
| `nucleus.middleware.brute_force_guard`                                       | 36   | proteção contra força bruta    |
| `nucleus.middleware.csrf_protection`                                         | 54   | proteção CSRF                  |
| `nucleus.middleware.rate_limiter`                                            | 28   | limitação de taxa              |
| `nucleus.rules.architecture.controller_and_usecase_must_use_named_contracts` | 75   | regra não registrada           |
| `nucleus.security.attempt_tracker`                                           | 39   | rastreamento de tentativas     |
| `nucleus.security.token`                                                     | 41   | emissão/validação de token     |
| `nucleus.security.url_guard`                                                 | 92   | validação de URL de saída      |
| `nucleus.upload.file_sanitizer`                                              | 29   | sanitização de nome de arquivo |
| `nucleus.upload.file_signatures`                                             | 74   | assinaturas de arquivo         |
| `nucleus.upload.file_validator`                                              | 66   | validação de upload            |
| `nucleus.upload.upload_policy`                                               | 65   | política de upload             |
| `nucleus.upload.uploaded_file`                                               | 14   | modelo de arquivo enviado      |
| `orbits.planets.user.repository.user_repository`                             | 6    | repositório de usuário         |

**Total:** 625 SLOC (9,98% dos 6.261 SLOC de produção).

**Leitura:** o conjunto é coerente — segurança de borda (força bruta, CSRF, rate limit, token, URL) e upload de arquivos. Isso sugere **funcionalidade ainda não conectada aos fluxos exercitados**, não código aleatório. É um achado arquitetural relevante: existem capacidades implementadas que os cenários não usam.

### 5.12.2 Por que 15 estático virou 14 em runtime

O módulo `observatory.records` estava na lista estática de não alcançáveis. Em runtime ele foi observado, porque é um **pacote-pai** carregado implicitamente quando um submódulo é importado. O grafo estático não materializa essa aresta. Portanto:

- a lista estática tinha 15 módulos com código;
- um foi refutado pela execução;
- restaram 14 confirmados ausentes nos três cenários.

Esse é um exemplo didático de por que **validação independente importa**: a análise estática estava correta para o grafo que construiu, mas o grafo não representava todas as importações reais.

### 5.12.3 Pacotes-pai implícitos

O Python carrega `nucleus.rules.architecture` quando importa uma regra específica, mesmo que ninguém tenha escrito `import nucleus.rules.architecture`. São 42 pacotes-pai nessa condição. Eles não têm código próprio (inicializadores vazios) e por isso não alteram a conclusão sobre SLOC, mas alteram a contagem de módulos observados.

**Consequência prática:** conte módulos e SLOC separadamente. “175 módulos observados” e “133 módulos com código” são afirmações diferentes.

### 5.12.4 O que a alcançabilidade não prova

- **Não prova código morto.** Um módulo pode ser API pública, extensão, comando de linha de comando (**CLI**) não exercitado ou caminho de erro raro.
- **Não prova cobertura.** Três cenários não executam rotas HTTP completas, middlewares ou jobs.
- **Não prova ausência de dependência dinâmica.** O tracing instrumenta `importlib`, mas não reflexão arbitrária, plugins ou código gerado em tempo de execução.
- **Não prova qualidade.** Um módulo alcançável pode estar mal projetado; um não alcançável pode ser o melhor código do projeto.

---

## Fechamento do bloco

- LCOM mede compartilhamento de estado, não coesão conceitual.
- 39 classes têm domínio válido; 97 não têm, e isso precisa ser declarado.
- A alcançabilidade estática dá candidatos; o runtime reduz e refuta candidatos.
- 14 módulos ausentes em runtime são um **achado**, não um veredito.

**Próximo:** [Capítulo 5C](capitulo-05c-complexidade-e-tamanho.md) — complexidade ciclomática, cognitiva, tamanho, Halstead e MI.
