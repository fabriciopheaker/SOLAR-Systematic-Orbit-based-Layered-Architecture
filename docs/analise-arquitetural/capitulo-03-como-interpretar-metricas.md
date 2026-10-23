# Capítulo 3 — Como interpretar métricas corretamente

> **Pergunta deste capítulo:** por que um número, sozinho, não responde se a arquitetura é boa ou ruim?

---

## 3.1 Métrica, medida e indicador

Uma **métrica** é uma regra que transforma um elemento em um número. Uma **medida** é o valor obtido ao aplicar a regra a um elemento específico. Um **indicador** é uma métrica usada para apoiar uma conclusão sobre um atributo de qualidade.

Exemplo:

- métrica: complexidade ciclomática;
- medida: CC = 10 para `ErrorExposureScanner._destination`;
- indicador: “essa função concentra o maior esforço de ramificação do projeto”.

A distinção parece acadêmica, mas evita conclusões erradas: a medida é um fato; o indicador é uma interpretação.

---

## 3.2 Valor absoluto, média, mediana, percentil e extremos

### 3.2.1 Valor absoluto

É o número bruto de um elemento. Exemplo: `project_validator` tem Ce = 49. O valor absoluto é útil para localizar um caso, mas não diz se 49 é muito ou pouco sem uma referência.

### 3.2.2 Média

Soma dividida pela quantidade. Exemplo com cinco funções de CC `[1, 1, 2, 10, 1]`:

\[
\text{média} = \frac{1 + 1 + 2 + 10 + 1}{5} = 3,0
\]

A média é sensível a valores extremos: uma única função com CC 10 puxa a média para cima. No SOLAR, a média de CC é 2,31 para 553 funções, mas isso não significa que todas estejam perto de 2.

### 3.2.3 Mediana

É o valor que divide a amostra ordenada ao meio. No exemplo `[1, 1, 1, 2, 10]`, a mediana é 1. A mediana resiste a extremos e descreve melhor o “caso típico”.

No SOLAR:

- CC: média 2,31, mediana 2;
- complexidade cognitiva: média 2,65, mediana 2;
- tamanho de função: média 16,6 linhas, mediana 13.

A diferença entre média e mediana indica assimetria: poucos casos puxam a média para cima.

### 3.2.4 Percentil

O percentil `p` é o valor abaixo do qual `p%` dos dados ficam. O **P90** é o valor que separa os 90% menores dos 10% maiores. No SOLAR:

- CC: P90 = 5; máximo = 10;
- complexidade cognitiva: P90 = 6; máximo = 18;
- tamanho de função: P90 = 35 linhas; máximo = 163.

O P90 ajuda a identificar a “cauda”: se o P90 é 5 e o máximo é 10, há um caso extremo; se o P90 é 5 e o máximo é 50, há um outlier muito mais grave.

### 3.2.5 Máximo e mínimo

O máximo mostra o pior caso; o mínimo, o menor valor. Um máximo alto isolado não é um problema por si, mas é um **candidato a inspeção**. No SOLAR, `_destination` tem CC 10 e complexidade cognitiva 18; é o único caso acima do limiar usual de 15.

**Erro comum:** olhar apenas a média e concluir “está tudo bem”. No SOLAR, a média de CC é baixa, mas existe um caso no limite do rank B. A média não o esconde completamente, mas suaviza sua relevância.

---

## 3.3 Distribuição de resultados

Uma **distribuição** mostra como os valores se espalham. Duas amostras podem ter a mesma média e distribuições completamente diferentes:

- `[2, 2, 2, 2, 2]` — média 2, sem variação;
- `[1, 1, 2, 3, 3]` — média 2, variação moderada;
- `[1, 1, 1, 1, 6]` — média 2, com um outlier.

No SOLAR, a distribuição de CC é fortemente concentrada à esquerda: 523 das 553 funções (94,6%) estão no rank A do Radon, e apenas 30 no rank B. Isso é mais informativo do que a média isolada.

**Como representar:** histogramas, tabelas de faixas (rank A/B/C...), contagens por faixa e o P90. A documentação usa tabelas de faixas e o P90.

---

## 3.4 Contagem e proporção

**Contagem** é o número absoluto; **proporção** é a contagem dividida pelo total.

Exemplo: 39 das 136 classes têm LCOM aplicável.

\[
\frac{39}{136} \approx 0,287 = 28,7\%
\]

A proporção é útil para comparar conjuntos de tamanhos diferentes. Mas ela precisa de denominador explícito: “39 classes” sem “de 136” é ambíguo; “39 de 136” é claro.

**Cuidado no SOLAR:** 148 módulos de produção têm código; 59 inicializadores de pacote não têm código e 1 arquivo está vazio. Dizer “10% dos módulos não são alcançáveis” exige dizer se o denominador é 208 (todos), 148 (com código) ou 6.265 SLOC. Nesta documentação, o denominador é sempre declarado.

---

## 3.5 Tendência

**Tendência** é a direção de mudança ao longo do tempo. Para medi-la, é preciso uma série histórica — várias medições em commits ou versões diferentes.

O SOLAR tem **uma única fotografia**. Portanto, não é possível afirmar tendência de melhora ou piora. “A dívida está diminuindo” seria uma hipótese, não um resultado.

---

## 3.6 Limite de referência e linha de base

**Limite de referência** é um valor externo usado como comparação. Exemplos:

- ranks do Radon: A (1–5), B (6–10), C (11–20), D (21–30), E (31–40), F (≥41);
- limiar padrão 15 da regra S3776 do Sonar para complexidade cognitiva.

Esses limites são **convenções de ferramenta**. Eles não são universais e não foram calibrados para o SOLAR. Usá-los como referência é aceitável **se a origem for declarada**; usá-los como veredito absoluto não é.

**Linha de base** é o valor medido no próprio projeto em um momento de referência. Serve para acompanhar evolução:

- CC média = 2,31; P90 = 5; máximo = 10;
- LCOM aplicável = 39 de 136; LCOM4 > 1 = 4;
- Ce máximo = 49; Ca máximo = 38;
- 306 arestas internas; 14 módulos ausentes em runtime.

Sem linha de base, um número isolado não permite dizer “melhorou” ou “piorou”. Com linha de base, é possível comparar versões futuras usando o mesmo método.

---

## 3.7 Falso positivo e falso negativo

- **Falso positivo:** a ferramenta acusa um problema que não existe. Exemplo no SOLAR: LCOM 15 em `Database`, que não tem atributos de instância; a fórmula produz `C(6,2) = 15` por construção.
- **Falso negativo:** a ferramenta não acusa um problema que existe. Exemplo: análise estática que não vê o ciclo dinâmico `Database ↔ user_model` e conclui “zero ciclos”.

Falsos positivos e negativos não são “falhas da ferramenta” apenas; são consequências de **definição, escopo e representação**. Uma métrica pode ser adequada para um tipo de classe e inadequada para outro.

---

## 3.8 Métrica aproximada

Uma **métrica aproximada** usa uma representação parcial do sistema. O CBO do SOLAR é aproximado por AST: conta classes referenciadas por nome, mas não resolve tipos, fábricas ou `getattr`. Isso é suficiente para comparar classes dentro do projeto, mas não para afirmar o valor absoluto de CBO como uma ferramenta tipada faria.

**Regra:** uma aproximação deve ser declarada como aproximação. O resultado pode ser útil, mas não pode ser apresentado como medição universal.

---

## 3.9 Validação independente

**Validação independente** significa recalcular com outro método ou outra implementação. No SOLAR:

- CC, LCOM1, LCOM4, CBO e cognitiva coincidiram com implementações independentes;
- o acoplamento coincidiu em 3 de 4 módulos; a diferença do quarto foi explicada por arestas dinâmicas;
- o MI foi recalculado com a API oficial do Radon (0 divergências).

Validar não é apenas repetir o mesmo script: é verificar se o método e a interpretação resistem a uma checagem diferente.

---

## 3.10 Correlação e causalidade

**Correlação** significa que dois valores variam juntos. **Causalidade** significa que um provoca o outro.

Exemplo: classes com mais métodos tendem a ter LCOM1 maior. Isso é **correlação**, em parte **matemática** (mais métodos = mais pares possíveis = `C(m,2)`). Não significa que “ter muitos métodos causa baixa coesão”; significa que a métrica cresce com o número de métodos por construção.

No SOLAR, `ErrorExposureScanner` tem LCOM1 = 89 porque tem 14 métodos e um único atributo; LCOM4 = 1 mostra que os métodos estão conectados por chamadas. Concluir “baixa coesão” a partir do LCOM1 seria confundir correlação com causalidade e ignorar o contexto.

**Regra:** antes de propor uma relação causal, pergunte se há mecanismo, evidência e alternativa. Um gráfico de dispersão não prova causa.

---

## 3.11 Contexto arquitetural

O mesmo número pode ter significados diferentes conforme o papel do elemento:

- `Kernel` tem CBO 15 e Ce 16: é um **composition root** (ponto de composição), que precisa conhecer muitos componentes para montar a aplicação. CBO alto é esperado.
- `project_validator` tem Ce 49: é um **registro de regras**, que precisa importar todas as regras. Fan-out alto é estrutural.
- `solar_exception` tem Ca 38: é uma **exceção-base**, um hub estável. Fan-in alto é esperado.

Sem contexto, os três seriam “violações” de limites genéricos. Com contexto, são características intencionais com custos de manutenção específicos.

---

## 3.12 Comparação entre projetos diferentes

Comparar o CBO do SOLAR com o de um sistema Java pode ser enganoso:

- linguagens diferentes têm mecanismos diferentes de dependência;
- ferramentas diferentes contam de formas diferentes;
- domínios diferentes têm complexidade intrínseca diferente;
- o SOLAR é uma arquitetura de referência com uma aplicação-exemplo mínima.

Comparações entre projetos só são válidas quando o **método**, o **escopo** e o **significado** são equivalentes. Caso contrário, a comparação é apenas uma coincidência numérica.

---

## 3.13 As quatro leituras possíveis de um resultado

| Leitura                            | Quando se aplica                                                                  | Exemplo no SOLAR                                        |
| ---------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Favorável no contexto avaliado** | o valor é compatível com o papel do elemento e não há evidência de risco          | CC mediana 2 nas funções de produção                    |
| **Merece investigação**            | o valor é atípico ou concentra risco, mas não há prova de defeito                 | `_destination` com cognitiva 18 e CC 10                 |
| **Risco potencial**                | há mecanismo plausível de dificuldade futura, confirmado por evidência estrutural | ciclo `Database ↔ user_model`; 14 módulos fora do fluxo |
| **Inconclusivo**                   | os dados não permitem decidir                                                     | impacto dos 14 módulos ausentes em outros fluxos        |
| **Não aplicável**                  | a fórmula não tem domínio válido                                                  | LCOM em `Database` (sem atributos de instância)         |
| **Pendente de validação**          | falta uma verificação necessária                                                  | CBO absoluto com resolução de tipos                     |

Essas categorias não são notas universais. São **rótulos de leitura** para organizar a discussão.

---

## 3.14 Erros comuns de interpretação

| Erro                                     | Por que é errado                     | Exemplo                                       |
| ---------------------------------------- | ------------------------------------ | --------------------------------------------- |
| “Média baixa = não há problema”          | a média esconde outliers             | CC média 2,31, mas máximo 10                  |
| “Valor alto = defeito”                   | depende do papel do elemento         | Ce 49 em um registro de regras                |
| “Zero ciclos = arquitetura saudável”     | o grafo pode estar incompleto        | ciclo dinâmico invisível ao AST               |
| “Não apareceu em runtime = código morto” | cobre apenas os cenários executados  | 14 módulos ausentes, mas possível API pública |
| “MI 100 = manutenibilidade perfeita”     | saturação por volume zero            | 110 módulos com MI 100                        |
| “Halstead zero = função trivial”         | a ferramenta não conta chamadas      | `ErrorLog` com 8 de 12 funções zeradas        |
| “LCOM alto = classe ruim”                | LCOM1 cresce com o número de métodos | `ErrorExposureScanner`: LCOM1 89, LCOM4 1     |
| “Duas medições iguais = validação”       | reproduzir não é validar             | mesmo script, mesmo viés                      |

---

## 3.15 Resumo do capítulo

- Média, mediana, P90 e máximo contam histórias diferentes; use mais de uma.
- Proporções precisam de denominador explícito.
- Tendência exige série histórica; o SOLAR tem uma fotografia.
- Limites de ferramenta não são leis universais.
- Falsos positivos e negativos são esperados; declare o método.
- Correlação não é causalidade; contexto é parte da métrica.
- Um resultado pode ser favorável, preocupante, inconclusivo ou não aplicável.

**Próximo capítulo:** as categorias de métricas e as perguntas que cada uma responde.
