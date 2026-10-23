# Plano de testes — Etapa 4: desempenho e escalabilidade

**Projeto:** SOLAR  
**Data:** 2026-10-23  
**Ambiente:** Windows 11, Python 3.14.7 (CPython), execução local em `127.0.0.1`  
**Artefatos:** `observatory/audits/etapa_4/`

---

## 1. Perguntas que a auditoria pretende responder

1. Qual é a latência de uma requisição de saúde e de uma criação de usuário em condições controladas?
2. Como a latência e a vazão se comportam quando a concorrência aumenta dentro de limites seguros?
3. A criação de usuário é dominada por CPU (hash bcrypt), por acesso ao banco ou por ambos?
4. Há sinais de contenção, saturação ou erros sob concorrência?
5. O que os resultados permitem concluir — e o que não permitem — sobre escalabilidade?

## 2. Escopo real descoberto no repositório

| Item                  | Constatação                                                                                                      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Entrada da aplicação  | `server.py` (`Server.run`) e `Kernel.mount()`                                                                    |
| Rotas HTTP existentes | `GET /solar/health`; `POST /examples/users`                                                                      |
| Persistência          | SQLAlchemy + SQLite (TEST) ou PostgreSQL (DEV/PROD); `Database` com uma sessão compartilhada                     |
| Banco isolado         | `TEST_DB_NAME=:memory:` no `.env`; para concorrência será usado arquivo SQLite temporário                        |
| Hash de senha         | `bcrypt` com custo padrão da biblioteca (`Password.hash`)                                                        |
| Middleware            | `RequestPipeline`, `SecurityHeaders`, `ErrorHandler`; rate limit/brute force/CSRF não estão ligados no `Kernel`  |
| Testes existentes     | `pytest` 9.1.1, suíte em `tests/`                                                                                |
| Ferramenta de carga   | não há `hey`, `wrk`, `ab`, `locust` ou `k6`; será usado gerador próprio com `http.client` e threads              |
| Monitoramento         | sem `psutil`; CPU/memória do processo serão lidos via API do Windows (`GetProcessTimes`, `GetProcessMemoryInfo`) |
| Dados                 | massa sintética, e-mails únicos com prefixo `bench-`, sem dados pessoais                                         |

**Lacuna identificada:** não há endpoint de leitura de usuários. O custo de leitura do banco será observado pelo caminho de e-mail duplicado (`POST` com e-mail existente), que faz consulta e não executa bcrypt.

**Lacuna identificada:** não há requisitos formais de desempenho no repositório. Os resultados serão apresentados como **linha de base observada**, sem metas inventadas.

## 3. Hipóteses

| ID  | Hipótese                                                                        | Como será avaliada                                                                        |
| --- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| H1  | `GET /solar/health` tem latência baixa e estável, sem acesso ao banco           | latência e vazão em concorrência 1–16                                                     |
| H2  | `POST /examples/users` é dominado pelo custo do bcrypt, não pela escrita SQLite | comparar criação válida, e-mail duplicado (só leitura) e e-mail inválido (sem banco/hash) |
| H3  | A sessão SQLAlchemy compartilhada e o SQLite impõem limites sob concorrência    | taxa de erro e latência por nível; verificar mensagens no log                             |
| H4  | A vazão de criação cresce menos que a de saúde ao aumentar a concorrência       | comparação de req/s entre níveis                                                          |
| H5  | O ambiente local não permite concluir escalabilidade horizontal                 | explicitar que só uma instância foi medida                                                |

## 4. Cenários

### Teste A — Referência

- `GET /solar/health`, concorrência 1, 240 requisições, após aquecimento de 30.
- `POST /examples/users` válido, concorrência 1, 20 requisições únicas.
- Medir: inicialização, latência média/mediana/P90/P95/P99, erros, CPU, memória, req/s.

### Teste B — Baixa carga

- `GET /solar/health`, concorrência 2, 240 requisições.
- `POST /examples/users` válido, concorrência 2, 20 requisições.
- Comparar com a referência e registrar variabilidade.

### Teste C — Concorrência controlada

- Saúde: concorrência 1, 2, 4, 8 e 16; 240 requisições por nível.
- Criação: concorrência 1, 2, 4 e 8; 20 requisições por nível.
- Registrar por nível: concluídas, falhas, latências, vazão, CPU, memória, timeouts e status inesperados.

### Teste D — Crescimento gradual

- Reutilizar os níveis do Teste C, comparando latência e vazão.
- O crescimento para se: taxa de erro > 20%, P95 > 5.000 ms ou processo sem responder por 10 s.

### Teste E — Persistência

- Criação válida: bcrypt + leitura + escrita.
- E-mail duplicado: leitura + regra de domínio, **sem** bcrypt.
- E-mail inválido: validação de domínio, **sem** banco e **sem** bcrypt.
- Saúde: sem banco.
- Comparar as medianas para separar custo de aplicação/hash do custo de persistência. Não atribuir toda a latência ao banco.

### Teste F — Comparação entre cenários

- Comparar saúde × criação, concorrência × vazão, leitura × escrita.
- Comparar níveis equivalentes; não comparar execuções com condições diferentes sem registrar o fator de confusão.
- Não há versão anterior nem segunda arquitetura: nenhuma comparação histórica será inventada.

## 5. Limites de segurança

| Recurso                  | Limite                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------ |
| Interface                | somente `127.0.0.1` (loopback)                                                       |
| Concorrência máxima      | 16 para saúde; 8 para escrita                                                        |
| Requisições por nível    | 240 (saúde); 20 (criação)                                                            |
| Timeout por requisição   | 10 s                                                                                 |
| Duração alvo por cenário | ≤ 30 s                                                                               |
| Dados                    | sintéticos; ≤ 300 usuários no banco temporário                                       |
| Banco                    | arquivo SQLite em `tmp/`, criado do zero; sem migração destrutiva em banco existente |
| Código de produção       | não será alterado                                                                    |
| Ambiente externo         | nenhum tráfego externo; nenhum serviço público                                       |
| Interrupção              | parar o aumento se houver erro > 20%, P95 > 5 s ou instabilidade do processo         |

## 6. Métricas e definições

- **Latência:** intervalo entre o início do envio no cliente e o término da leitura da resposta HTTP. Inclui conexão TCP na primeira requisição de cada worker e o tempo de rede local; não é o tempo interno isolado da aplicação.
- **Vazão:** requisições concluídas ÷ duração da janela medida (req/s).
- **Concorrência:** número de workers com requisição em andamento; não é o total de requisições.
- **P50/P90/P95/P99:** percentis pelo método do posto mais próximo (`nearest-rank`) sobre as respostas esperadas.
- **Taxa de erros:** respostas inesperadas, timeouts e exceções ÷ total.
- **CPU:** variação do tempo de CPU do processo do servidor ÷ tempo de parede × 100 (equivalente a um núcleo; pode passar de 100% em multithread).
- **Memória:** working set do processo do servidor, amostrado a cada 100 ms; máximo e média.
- **Saturação:** latência crescente + vazão estagnada + erros/recursos no limite. Isoladamente, cada sinal é indício, não prova.

## 7. Metodologia

1. Verificação funcional: subir a aplicação isolada e confirmar `GET /solar/health` e `POST /examples/users`.
2. Aquecimento: 30 requisições de saúde e 1 criação, descartadas das estatísticas.
3. Executar os níveis em ordem crescente, com pausa curta entre eles.
4. Preservar todas as amostras brutas em CSV; não descartar amostras desfavoráveis.
5. Calcular indicadores a partir das amostras, não de estimativas.
6. Registrar logs do servidor e metadados do ambiente.
7. Parar e documentar qualquer falha, timeout ou degradação abrupta.

## 8. Reprodutibilidade

- Comando principal: `py observatory/audits/etapa_4/run_benchmark.py`.
- O script cria ambiente temporário, banco SQLite próprio, `.env` temporário e storage temporário.
- O servidor escuta em porta efêmera de loopback e é encerrado ao fim.
- Versões e comandos são gravados em `RESULTADOS_BRUTOS/environment.json`.
- O código de produção não é modificado; os scripts de teste vivem apenas em `observatory/audits/etapa_4/`.

## 9. O que não será testado

- PostgreSQL real (o ambiente local não tem instância isolada disponível).
- Múltiplas instâncias, balanceamento de carga ou escalabilidade horizontal.
- Rate limiting, brute force e CSRF (não estão ligados no `Kernel` atual).
- Cobertura funcional completa, testes de caos, testes de longa duração e esgotamento de recursos.
- Comparação histórica: não existe versão anterior medida com o mesmo método.
