# Capítulo 4 — Categorias das métricas e análises

> **Pergunta deste capítulo:** como organizar dezenas de métricas em grupos que respondem a perguntas parecidas?

---

## 4.1 Por que categorizar

Uma lista de métricas sem organização vira um catálogo confuso. Categorizar ajuda a:

- escolher a métrica certa para a pergunta;
- evitar usar uma métrica para um fim que ela não tem;
- perceber sobreposições (a mesma métrica pode servir a mais de uma categoria);
- reconhecer que uma categoria não é uma ferramenta nem um teste.

**Aviso:** uma métrica pode pertencer a mais de uma categoria. O CBO, por exemplo, é uma métrica de acoplamento, mas também informa sobre manutenibilidade. Isso não é erro; é sobreposição legítima.

---

## 4.2 As oito categorias usadas nesta documentação

### 4.2.1 Dependências e acoplamento

**Pergunta:** quem depende de quem, quanto e em que direção?

**Métricas:** fan-in (Ca), fan-out (Ce), instabilidade (I), CBO, densidade do grafo, dependências por camada.

**O que ajuda a responder:** hubs, pontos de impacto, direção das dependências, risco de mudança.

**O que não responde:** se a dependência é intencional ou se o contrato é bom.

### 4.2.2 Coesão

**Pergunta:** as responsabilidades de uma classe estão relacionadas?

**Métricas:** LCOM1, LCOM4, LCOM\*, TCC, contagem de atributos e métodos.

**O que ajuda a responder:** classes que acumulam responsabilidades, classes de estado mínimo, classes funcionais.

**O que não responde:** se a classe está no lugar certo da arquitetura, nem se o nome e o contrato fazem sentido.

### 4.2.3 Complexidade

**Pergunta:** quanto esforço de controle e de leitura o código exige?

**Métricas:** complexidade ciclomática (CC), complexidade cognitiva, profundidade de aninhamento, número de ramos.

**O que ajuda a responder:** funções candidatas a revisão, concentração de esforço, testabilidade.

**O que não responde:** qualidade da arquitetura global, corretude, clareza dos nomes.

### 4.2.4 Tamanho

**Pergunta:** quanto código existe em cada unidade?

**Métricas:** LOC, SLOC, LLOC, linhas por função, linhas por módulo, NOM (número de métodos), NOC (número de classes).

**O que ajuda a responder:** unidades extensas, concentração de código, esforço de leitura.

**O que não responde:** se o tamanho é justificado pelo domínio ou se a unidade está bem separada.

### 4.2.5 Manutenibilidade

**Pergunta:** o código é fácil de manter?

**Métricas:** MI, combinações de CC + Halstead + tamanho, indicadores de legibilidade.

**O que ajuda a responder:** comparação descritiva entre módulos, quando a métrica tem poder de discriminação.

**O que não responde:** tempo real de manutenção, custo de mudança, qualidade percebida por quem mantém.

### 4.2.6 Ciclos de dependência

**Pergunta:** há caminhos circulares de dependência?

**Métricas:** SCCs, número de ciclos, tamanho do maior ciclo, arestas internas ao SCC.

**O que ajuda a responder:** riscos de inicialização, dificuldade de teste isolado, acoplamento bidirecional.

**O que não responde:** se o ciclo é intencional, se há defeito funcional, se o ciclo é inevitável no domínio.

### 4.2.7 Alcance e utilização

**Pergunta:** quais módulos são alcançáveis a partir dos pontos de entrada? Quais nunca foram vistos em execução?

**Métricas:** BFS de alcançabilidade, módulos não alcançáveis, módulos observados em runtime, diferença estático × dinâmico.

**O que ajuda a responder:** candidatos a código não utilizado, cobertura de cenários, dependências dinâmicas.

**O que não responde:** se um módulo é código morto; ausência de evidência não é prova de ausência.

### 4.2.8 Análises complementares

**Pergunta:** o que mais foi efetivamente medido e não cabe nas categorias anteriores?

**Exemplos no SOLAR:** reprodutibilidade, determinismo, auditoria do relatório estrutural original, validação independente, tracing de importações, regras arquiteturais verificadas pelo `ProjectValidator`.

**O que ajuda a responder:** confiança nos resultados, consistência entre ferramentas, lacunas de método.

---

## 4.3 Tabela-síntese

| Categoria                  | Perguntas principais                          | Métricas e análises                                     | Onde no SOLAR                                            |
| -------------------------- | --------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| Dependências e acoplamento | quem usa quem? quantos? em que direção?       | Ca, Ce, I, CBO, matriz de camadas                       | `solar_acoplamento_modulos.csv`, `matriz_camadas.csv`    |
| Coesão                     | os métodos compartilham estado?               | LCOM1, LCOM4, LCOM\*, TCC                               | `coesao_classes.csv`                                     |
| Complexidade               | quantos caminhos e quanto esforço de leitura? | CC, cognitiva, ramos, aninhamento                       | `funcoes_complexidade.csv`, `complexidade_cognitiva.csv` |
| Tamanho                    | quanto código por unidade?                    | LOC, SLOC, LLOC, linhas/função, NOM, NOC                | `tamanho.json`, `modulos_metricas.csv`                   |
| Manutenibilidade           | o código é fácil de manter?                   | MI, sensibilidade do MI                                 | `manutenibilidade.json`, `modulos_metricas.csv`          |
| Ciclos                     | há caminhos circulares?                       | SCCs, ciclos, arestas internas                          | `solar_ciclos_internos.json`                             |
| Alcance e utilização       | o que é alcançável e o que foi observado?     | BFS, módulos não alcançáveis, tracing                   | `alcancabilidade.json`, `runtime_tracing/`               |
| Análises complementares    | os resultados são confiáveis?                 | reprodutibilidade, determinismo, auditoria do relatório | `verificacoes.json`, `alertas_estruturais_revisados.csv` |

---

## 4.4 Categoria não é métrica, ferramenta, teste ou resultado

| Termo          | Exemplo                        | O que é                                |
| -------------- | ------------------------------ | -------------------------------------- |
| **Categoria**  | acoplamento                    | grupo de métricas com finalidade comum |
| **Métrica**    | fan-in                         | regra que produz um número             |
| **Ferramenta** | Radon                          | software que calcula métricas          |
| **Teste**      | teste de rota                  | verificação de comportamento           |
| **Resultado**  | Ca = 38 para `solar_exception` | valor observado em um elemento         |

Misturar esses níveis produz frases como “o Radon é um teste de acoplamento” (errado: é uma ferramenta de métricas) ou “o fan-in passou” (métricas não “passam”; elas produzem valores).

---

## 4.5 Como escolher a categoria certa

1. **Se a pergunta é “o que depende do quê?”** → dependências e acoplamento.
2. **Se a pergunta é “esta classe faz coisas demais?”** → coesão.
3. **Se a pergunta é “esta função é difícil de testar/ler?”** → complexidade.
4. **Se a pergunta é “este arquivo é grande demais?”** → tamanho.
5. **Se a pergunta é “este código é sustentável?”** → manutenibilidade (com ressalvas).
6. **Se a pergunta é “há emaranhamento circular?”** → ciclos.
7. **Se a pergunta é “isto é usado?”** → alcance e utilização.
8. **Se a pergunta é “posso confiar no número?”** → análises complementares.

---

## 4.6 Resumo do capítulo

- Oito categorias organizam as métricas por pergunta.
- Categorias podem se sobrepor; isso é normal.
- Categoria, métrica, ferramenta, teste e resultado são níveis diferentes.
- Nenhuma categoria responde sozinha se a arquitetura é “boa”.
- A escolha da categoria deve vir da pergunta, não da ferramenta disponível.

**Próximo capítulo:** o catálogo detalhado, começando por fan-in, fan-out, instabilidade e CBO.
