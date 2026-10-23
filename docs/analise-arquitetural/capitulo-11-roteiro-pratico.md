# Capítulo 11 — Roteiro prático

> **Objetivo:** permitir que outra pessoa reproduza a análise e chegue às mesmas conclusões — ou descubra onde elas falham.

---

## 11.1 Pré-requisitos

| Item                              | Verificação                                  |
| --------------------------------- | -------------------------------------------- |
| Python 3.14+                      | `py --version`                               |
| Radon 6.0.1                       | `py -m pip show radon`                       |
| flake8 7.4.1                      | `py -m pip show flake8`                      |
| flake8-cognitive-complexity 0.1.0 | `py -m pip show flake8-cognitive-complexity` |
| Dependências da aplicação         | `py -m pip install -r requirements.txt`      |
| Terminal na raiz do projeto       | `Get-Location` deve terminar em `\SOLAR`     |

**Observação do ambiente:** não há `python` no PATH; use `py`. Todos os comandos abaixo são PowerShell.

---

## 11.2 Passo a passo

### Passo 1 — Confirmar o ambiente

```powershell
py --version
py -m pip show radon flake8 flake8-cognitive-complexity
```

**Evidência esperada:** versões 3.14.x, 6.0.1, 7.4.1 e 0.1.0. Se as versões forem outras, os números podem mudar; registre-as.

### Passo 2 — Definir o escopo antes de medir

Decida e registre:

- produção = tudo fora de `tests/`;
- testes = `tests/`;
- `htmlcov/` e `reports/` não entram no corpus;
- “módulo” = arquivo `.py` importável.

Sem esse passo, médias e volumes misturam conjuntos e as conclusões ficam ambíguas.

### Passo 3 — Gerar as métricas

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py --root . --out observatory/audits/etapa_2_acoplamento_coesao/dados --out-complexity observatory/audits/etapa_3_complexidade/dados
```

**Saídas principais:** `resumo_metricas.json`, `modulos_metricas.csv`, `modulos_acoplamento.csv`, `coesao_classes.csv`, `funcoes_complexidade.csv`, `complexidade_cognitiva.csv`, `radon_halstead_modulos.csv`, `alcancabilidade.json`, `solar_ciclos_internos.json`.

**Conferência rápida:**

```powershell
py -c "import json; d=json.load(open('observatory/audits/etapa_2_acoplamento_coesao/dados/resumo_metricas.json',encoding='utf-8')); print(d['production_modules'], d['internal_edges'], d['complexity']['cc_total_production']['sum'])"
```

Esperado: `208 306 1278`.

### Passo 4 — Ler o resumo antes dos detalhes

Abra `observatory/audits/etapa_2_acoplamento_coesao/dados/resumo_metricas.json` e confira:

- `production_modules` = 208;
- `internal_edges` = 306;
- `complexity.cc_total_production.n` = 553;
- `maintainability.mi_production.n` = 208;
- `coupling` e `classes` presentes.

Se algum bloco estiver ausente, o script não terminou; não interprete resultados parciais.

### Passo 5 — Auditar os alertas originais

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/scripts/revisar_relatorio.py
```

**Saída:** `alertas_estruturais_revisados.csv` com veredictos por alerta.

**Conferência:** 60 linhas; contagem de veredictos deve ser 7 confirmados, 7 falsos positivos, 43 parciais, 1 não reproduzível e 2 fora de escopo.

### Passo 6 — Validação independente

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/evidencias/verificacoes_independentes.py
```

**O que faz:** recalcula CC, LCOM, CBO, cognitiva, Halstead e MI por implementações independentes.

**Conferência:** o relatório deve indicar V1–V9 com os valores esperados (CC 553/1.278/10; cognitiva 794/18; MI 0 divergências).

### Passo 7 — Tracing de runtime

```powershell
py observatory/audits/etapa_2_acoplamento_coesao/evidencias/runtime_tracing/trace_imports.py --all
```

**Saídas:** `imports_runtime_verificador.json`, `imports_runtime_bootstrap.json`, `imports_runtime_modelo_isolado.json`, `comparacao_alcancabilidade.json`, `verificador_stdout.txt`.

**Conferência:**

- cenário A: 85 módulos SOLAR, saída 0;
- cenário B: 172 módulos, `mount()` concluído;
- cenário C: 13 módulos, `AttributeError`;
- união: 175 módulos; 14 ausentes; 1 refutado (`observatory.log`).

### Passo 8 — Rodar o validador arquitetural

```powershell
py observatory/solar check
```

**Saída esperada:** `correct` com 17 verificações, 29 regras e 0 violações; auditoria gravada em `observatory/audits/etapa_1_conformidade/evidencias/check/`.

**Cuidado:** o comando grava um arquivo de auditoria. Para uma análise que não deve alterar o repositório, rode em uma cópia ou aponte o diretório de auditoria para fora do projeto.

### Passo 9 — Inspecionar os outliers no código

Não confie apenas no CSV. Leia:

- `nucleus/rules/scanner/error_exposure_scanner.py` (`_destination`);
- `nucleus/kernel.py` (`mount`);
- `nucleus/database/drivers/driver_sqlalchemy.py`;
- `nucleus/database/database.py` e `orbits/database/models/user_model.py`;
- `nucleus/security/token.py`.

**Pergunta-guia:** o valor é explicado pelo papel do elemento ou revela uma responsabilidade inesperada?

### Passo 10 — Registrar conclusões com status

Para cada achado, registre:

| Campo         | Exemplo                                    |
| ------------- | ------------------------------------------ |
| Métrica       | cognitiva                                  |
| Valor         | 18                                         |
| Escopo        | `_destination`, produção                   |
| Status        | validado com ressalvas                     |
| Leitura       | merece investigação                        |
| Limite        | sem dados de cobertura de teste            |
| Próximo passo | inspecionar testes e complexidade de dados |

---

## 11.3 Exemplo aplicado 1 — `nucleus.security.token`

### Pergunta

O módulo de token é usado pela aplicação?

### Comandos

```powershell
py -c "from radon.raw import analyze; print(analyze(open('nucleus/security/token.py',encoding='utf-8').read()).sloc)"
Get-ChildItem -Path nucleus,orbits,observatory,server.py -Recurse -Filter *.py |
  Select-String -Pattern "nucleus.security.token"
Get-ChildItem -Path tests -Recurse -Filter *.py |
  Select-String -Pattern "nucleus.security.token"
py -c "import json; d=json.load(open('observatory/audits/etapa_2_acoplamento_coesao/dados/alcancabilidade.json',encoding='utf-8')); print([m['module'] for m in d['nao_alcancaveis_com_codigo'] if 'token' in m['module']])"
```

### Evidências

| Evidência                    | Resultado                                                         |
| ---------------------------- | ----------------------------------------------------------------- |
| Arquivo existe               | 41 SLOC                                                           |
| Import em produção           | **nenhum**                                                        |
| Import em testes             | `tests/rules/test_controller_security_scanner.py` importa `Token` |
| Ca / Ce                      | 0 / 0                                                             |
| Alcançável estaticamente     | **não**                                                           |
| Observado nos cenários A/B/C | **não**                                                           |
| Lista de ausentes            | presente (14 módulos)                                             |

### Leitura

- O módulo **é usado por teste**, então não é código morto.
- Não é carregado pela aplicação em nenhum dos três cenários.
- O conjunto de 14 ausentes é coerente: segurança de borda e upload.

### Conclusão

**Risco potencial:** existe uma capacidade de token que a aplicação não conecta nos fluxos exercitados. Isso pode ser:

1. funcionalidade planejada e ainda não integrada;
2. uso previsto apenas por testes/consumidores externos;
3. código obsoleto.

**O que não se pode concluir:** que é inútil. **Próximo passo:** decidir, com o dono do produto, se o token deve ser usado por middleware/rotas ou removido. Nenhuma alteração deve ser feita apenas com base na métrica.

---

## 11.4 Exemplo aplicado 2 — `SOLAR-ROF-003`

### Pergunta

O validador verifica a regra de contratos nomeados?

### Comandos

```powershell
Get-ChildItem -Path nucleus/rules -Recurse -Filter *.py |
  Select-String -Pattern "SOLAR-ROF-003"
Get-ChildItem -Path nucleus/rules -Recurse -Filter *.py |
  Select-String -Pattern "ControllerAndUseCaseMustUseNamedContracts"
Select-String -Path nucleus/rules/project_validator.py -Pattern "ControllerAndUseCaseMustUseNamedContracts"
py observatory/solar check
```

### Evidências

| Evidência                         | Resultado                                         |
| --------------------------------- | ------------------------------------------------- |
| Classe da regra existe            | `ControllerAndUseCaseMustUseNamedContracts`       |
| Código declarado                  | `SOLAR-ROF-003`                                   |
| Aparece em `project_validator.py` | **não**                                           |
| Teste unitário da regra           | **sim** (`observatory/tests/rules/architecture/`) |
| Regras executadas                 | 29                                                |
| Resultado do validador            | `correct`, 0 violações                            |
| Documentação do projeto           | confirma que ROF-003 não tem scanner              |

### Leitura

- A regra tem classe e teste unitário, mas não tem scanner e não está entre as 29 executadas.
- O resultado `correct` é verdadeiro **para o conjunto executado**.
- “0 violações” não cobre ROF-003 no `check`.
- A ausência de scanner não é evidência de violação, nem de problema de persistência.

### Conclusão

**Pendente de validação:** a conformidade é parcial por construção. **Próximo passo:** implementar o scanner da ROF-003 e registrá-lo no validador; só então “0 violações” passará a incluir a regra.

**O que não se pode concluir:** que a regra é violada. Não há evidência de violação; há ausência de verificação.

---

## 11.5 Erros de processo a evitar

| Erro                                            | Por que é ruim                | Como evitar               |
| ----------------------------------------------- | ----------------------------- | ------------------------- |
| Rodar Radon na raiz sem excluir `tests/`        | mistura produção e teste      | filtrar `tests.`          |
| Comparar Ce de módulos diferentes sem escopo    | números incomparáveis         | declarar interno/externo  |
| Aplicar LCOM a classes sem atributos            | falso positivo por construção | checar aplicabilidade     |
| Concluir “código morto” por ausência em runtime | ausência ≠ morte              | cruzar com testes/API     |
| Usar MI para ordenar módulos                    | saturação                     | usar CC/cognitiva/tamanho |
| Ignorar regras sem scanner                      | conformidade parcial          | auditar o registro        |
| Apresentar aproximação como exatidão            | conclusão inválida            | declarar método           |
| Não registrar versões                           | irreprodutibilidade           | registrar ambiente        |

---

## 11.6 Checklist de reprodução

- [ ] Versões registradas.
- [ ] Escopo produção/teste declarado.
- [ ] `resumo_metricas.json` com 208 módulos e 306 arestas.
- [ ] CC total 1.278, máximo 10.
- [ ] Cognitiva total 794, máximo 18.
- [ ] LCOM aplicável 39; N/A 97.
- [ ] CBO máximo 15; 0 ambíguos.
- [ ] MI 269 rank A; 110 módulos de produção com 100.
- [ ] 0 ciclos estáticos; 1 ciclo dinâmico.
- [ ] 14 ausentes em runtime; 1 refutado.
- [ ] 60 alertas revisados com a distribuição esperada.
- [ ] Validador `correct` com 29 regras.
- [ ] Outliers lidos no código.
- [ ] Conclusões com status e limitações.

---

## 11.7 Resumo do capítulo

- O roteiro tem 10 passos: ambiente, escopo, métricas, resumo, auditoria, validação, runtime, validador, leitura e registro.
- Os dois exemplos mostram como sair do número para a evidência e da evidência para uma conclusão limitada.
- Nenhum exemplo altera código de produção.
- Nenhuma conclusão dispensa leitura humana.

**Próximo:** [Capítulo 12](capitulo-12-conclusao-referencias.md) — conclusão e referências.
