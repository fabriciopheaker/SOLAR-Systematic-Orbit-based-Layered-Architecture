# Capítulo 9 — Classificação dos resultados

> **Pergunta deste capítulo:** como dizer se um número é “bom”, “preocupante” ou “inconclusivo” sem inventar limites universais?

---

## 9.1 O problema dos limites universais

É tentador dizer:

- “CC acima de 10 é ruim”;
- “CBO acima de 5 é violação”;
- “LCOM acima de 20 é classe ruim”;
- “MI abaixo de 20 é código não mantenível”.

Esses números existem em ferramentas e livros, mas **não são leis**. Eles dependem de:

- linguagem e paradigma;
- domínio e criticidade;
- tamanho e maturidade do projeto;
- definição exata da métrica;
- objetivo da análise.

No SOLAR, usar um limite universal produziria conclusões falsas: `Kernel` tem CBO 15 por ser composition root; `project_validator` tem Ce 49 por ser registro de regras. Nenhum dos dois é “violação” por esse motivo.

---

## 9.2 Classificação contextual

Em vez de “bom/ruim”, esta documentação usa sete rótulos:

| Rótulo                    | Significado                                                            | Critério                                            |
| ------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| **Favorável no contexto** | o valor é compatível com o papel e não há evidência de risco           | distribuição + papel + ausência de achado contrário |
| **Merece investigação**   | atípico ou concentra risco, mas não há prova de problema               | outlier + combinação de métricas                    |
| **Risco potencial**       | há mecanismo plausível de dificuldade futura, com evidência estrutural | achado confirmado + mecanismo                       |
| **Inconclusivo**          | os dados não permitem decidir                                          | lacuna de método/cobertura                          |
| **Não aplicável**         | a fórmula não tem domínio válido                                       | pré-condição não atendida                           |
| **Pendente de validação** | falta uma verificação necessária                                       | método não executado                                |
| **Informativo**           | verificação de conformidade, não métrica                               | saída binária/qualitativa                           |

**Nenhum rótulo é uma nota.** São formas de organizar a discussão e priorizar leitura.

---

## 9.3 Aplicação aos resultados do SOLAR

### 9.3.1 Acoplamento

| Resultado                    | Rótulo                   | Justificativa                      | O que mudaria o rótulo                   |
| ---------------------------- | ------------------------ | ---------------------------------- | ---------------------------------------- |
| Ca 38 em `solar_exception`   | favorável no contexto    | exceção-base; muitos dependem dela | contrato instável ou mudanças frequentes |
| Ce 49 em `project_validator` | favorável no contexto    | registro de regras                 | regras de negócio misturadas ao registro |
| Ce 16 em `Kernel`            | favorável no contexto    | composition root                   | lógica de negócio no Kernel              |
| CBO 15 em `Kernel`           | merece investigação leve | alto, mas explicado pelo papel     | crescimento sem justificativa            |
| CBO médio 1,54               | favorável no contexto    | baixo para 136 classes             | aumento generalizado                     |
| 107 módulos com Ce 0         | inconclusivo             | podem ser folhas ou não usados     | análise de uso                           |
| 70 módulos com Ca 0          | inconclusivo             | inits, testes, API pública         | confirmação de uso                       |
| I indefinido em 60           | não aplicável            | `Ca + Ce = 0`                      | conexão do módulo                        |

### 9.3.2 Coesão

| Resultado                                     | Rótulo                | Justificativa                         | O que mudaria o rótulo               |
| --------------------------------------------- | --------------------- | ------------------------------------- | ------------------------------------ |
| LCOM4 = 3 em `DriverSQLAlchemy`               | merece investigação   | 3 grupos de métodos com estado        | inspeção mostrar 3 responsabilidades |
| LCOM4 = 2 em `Kernel`                         | favorável no contexto | composition root com grupos           | lógica de negócio nos grupos         |
| LCOM4 = 2 em `ErrorLog`                       | merece investigação   | dois grupos                           | confirmar se são dois usos           |
| LCOM1 89 em `ErrorExposureScanner`            | inconclusivo          | alto por número de métodos; LCOM4 = 1 | estado compartilhado real            |
| LCOM em `Database`/`Storage`/`DatabaseDriver` | não aplicável         | sem atributos de instância            | surgimento de estado                 |
| 97 classes N/A                                | não aplicável         | pré-condição não atendida             | redesenho com estado                 |

### 9.3.3 Complexidade

| Resultado                      | Rótulo                   | Justificativa      | O que mudaria o rótulo             |
| ------------------------------ | ------------------------ | ------------------ | ---------------------------------- |
| CC mediana 2                   | favorável no contexto    | maioria simples    | aumento da mediana                 |
| CC 10 em `_destination`        | merece investigação      | maior CC, rank B   | testes/refatoração mostrarem custo |
| Cognitiva 18 em `_destination` | merece investigação      | único > 15         | combinação com baixa testabilidade |
| Cognitiva 14/13                | merece investigação leve | próximos do limiar | crescimento                        |
| 523 funções rank A             | favorável no contexto    | 94,6%              | queda da proporção                 |
| Ramos 22/35                    | inconclusivo             | detalhe parcial    | reprodutibilidade total            |

### 9.3.4 Tamanho

| Resultado                 | Rótulo                | Justificativa         | O que mudaria o rótulo            |
| ------------------------- | --------------------- | --------------------- | --------------------------------- |
| `Kernel.mount` 163 linhas | merece investigação   | longo, mas CC 2       | crescimento ou lógica condicional |
| `_scan_file` 108 linhas   | merece investigação   | longo e CC 6          | acúmulo de casos                  |
| Mediana 13 linhas         | favorável no contexto | típico                | aumento                           |
| 76 funções > 30           | favorável no contexto | 13,7%                 | aumento expressivo                |
| NOC 136                   | favorável no contexto | projeto pequeno/médio | crescimento sem separação         |

### 9.3.5 Manutenibilidade

| Resultado                | Rótulo              | Justificativa          | O que mudaria o rótulo  |
| ------------------------ | ------------------- | ---------------------- | ----------------------- |
| MI 100 em 110 módulos    | inconclusivo        | saturação              | volume calculável       |
| MI 32,26 em `http_input` | inconclusivo        | sensível a comentários | MI sem comentários      |
| MI médio 88,14           | inconclusivo        | composto saturado      | métricas complementares |
| Δ máximo 47,62           | merece investigação | sensibilidade alta     | fórmula estável         |

### 9.3.6 Ciclos e alcance

| Resultado                      | Rótulo                         | Justificativa                   | O que mudaria o rótulo          |
| ------------------------------ | ------------------------------ | ------------------------------- | ------------------------------- |
| 1 ciclo dinâmico               | risco potencial                | dependência de ordem confirmada | falha em inicialização ou teste |
| 0 ciclos estáticos             | favorável no contexto avaliado | grafo acíclico no modelo        | novos imports                   |
| 14 módulos ausentes            | risco potencial                | 625 SLOC não exercitados        | confirmação de uso/abandono     |
| `observatory.records` refutado | favorável no contexto          | pacote-pai carregado            | —                               |
| 42 pais implícitos             | não aplicável                  | inits vazios                    | —                               |

### 9.3.7 Conformidade

| Resultado               | Rótulo                         | Justificativa        | O que mudaria o rótulo   |
| ----------------------- | ------------------------------ | -------------------- | ------------------------ |
| 0 violações / 29 regras | favorável no contexto avaliado | regras ativas passam | violação ou regra nova   |
| ROF-003 sem scanner     | pendente de validação          | regra não executada  | implementação do scanner |

---

## 9.4 Prioridade não é severidade

Uma classificação útil responde “o que ler primeiro?”, não “qual é a nota”. Critérios práticos:

1. **Evidência:** o achado foi confirmado por mais de um método?
2. **Impacto:** quantos módulos/usuários dependem disso?
3. **Mecanismo:** existe uma explicação plausível de como isso causa dificuldade?
4. **Custo:** a correção é viável?
5. **Incerteza:** o que ainda não se sabe?

Aplicando ao SOLAR:

| Achado                        | Evidência          | Impacto                 | Mecanismo                    | Incerteza    | Prioridade de leitura |
| ----------------------------- | ------------------ | ----------------------- | ---------------------------- | ------------ | --------------------- |
| 14 módulos ausentes           | estático + runtime | alto (segurança/upload) | funcionalidade não conectada | uso externo? | **alta**              |
| ciclo `Database ↔ user_model` | runtime + estático | médio                   | ordem de inicialização       | falha real?  | **alta**              |
| `_destination` cognitiva 18   | duas métricas      | baixo/médio             | leitura/teste                | cobertura?   | **média**             |
| CBO 15 `Kernel`               | métrica + papel    | baixo                   | composição                   | crescimento? | **média**             |
| MI saturado                   | fórmula            | baixo                   | volume zero                  | —            | **baixa**             |
| LCOM 15 `Database`            | falso positivo     | nenhum                  | N/A                          | —            | **nenhuma**           |

**Prioridade alta** não significa “defeito”; significa “merece leitura primeiro”.

---

## 9.5 Limites de ferramenta como referência, não veredito

| Referência              | Origem                  | Uso aceitável          | Uso inadequado                         |
| ----------------------- | ----------------------- | ---------------------- | -------------------------------------- |
| Rank A–F (Radon)        | convenção da ferramenta | descrever faixas de CC | dizer que rank B é “defeito”           |
| Limiar 15 (Sonar S3776) | convenção da regra      | sinalizar candidatos   | afirmar que 16 é “ruim” universalmente |
| MI A > 19               | convenção do Radon      | triagem                | afirmar manutenibilidade real          |
| “CBO ≤ 5”               | heurística comum        | conversa inicial       | violação arquitetural                  |
| “LCOM ≤ 20”             | heurística comum        | conversa inicial       | prova de baixa coesão                  |

**Regra:** sempre cite a origem do limite e o que ele significa. Sem origem, o limite é opinião.

---

## 9.6 Como criar uma linha de base útil

1. **Fixe o método:** mesmas ferramentas, versões e filtros.
2. **Fixe o escopo:** produção separada de testes.
3. **Registre distribuições:** mediana, P90, máximo e contagens por faixa.
4. **Registre os outliers com contexto:** nome, papel, valor.
5. **Registre o que é N/A:** não esconda os 97 casos de LCOM.
6. **Registre as lacunas:** Halstead incompleto, MI saturado, CBO aproximado.
7. **Compare versões futuras com a mesma régua.**

Linha de base do SOLAR (resumo):

| Indicador                          | Valor de referência |
| ---------------------------------- | ------------------- |
| CC mediana / P90 / máximo          | 2 / 5 / 10          |
| Cognitiva mediana / máximo         | 2 / 18              |
| Funções > 30 / > 50 / > 100 linhas | 76 / 12 / 2         |
| CBO médio / máximo                 | 1,54 / 15           |
| Ce mediano / máximo                | 3 / 49              |
| Ca máximo                          | 38                  |
| LCOM aplicável                     | 39 de 136           |
| LCOM4 > 1                          | 4                   |
| MI = 100                           | 110 de 208          |
| Ciclos dinâmicos                   | 1                   |
| Ausentes em runtime                | 14 (625 SLOC)       |

---

## 9.7 O que **não** classificar

- **Não classifique módulos N/A como ruins.** `Database` não tem LCOM porque não tem estado de instância.
- **Não classifique zeros de Halstead como triviais.** São falha de representação.
- **Não classifique ausência em runtime como código morto.** É ausência de evidência.
- **Não classifique MI 100 como excelência.** É saturação.
- **Não classifique 0 violações como conformidade total.** Há regra sem scanner.

---

## 9.8 Resumo do capítulo

- Limites universais não existem; existem convenções e contexto.
- Sete rótulos organizam a leitura sem transformar métrica em nota.
- Prioridade combina evidência, impacto, mecanismo, custo e incerteza.
- Referências de ferramenta devem ser citadas como referências, não como leis.
- Uma linha de base útil registra método, escopo, distribuição, outliers, N/A e lacunas.

**Próximo:** [Capítulo 10](capitulo-10-limitacoes.md) — as limitações do método e dos resultados.
