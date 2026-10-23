# Observatory

### 1. Definição

O Observatory é a consciência arquitetural da SOLAR.

Ele concentra o que **olha** para a aplicação sem participar dela.

Seu papel é registrar o que a arquitetura está de fato se tornando, e não o que ela deveria ser.

O Observatory não representa um estágio do processamento.

Ele representa a observação.

### 2. Responsabilidades

O Observatory é responsável por:

verificação das regras arquiteturais;

registro (auditoria) dos resultados;

histórico das verificações;

evidência para revisão e para a integração contínua.

### 3. Não responsabilidades

Não pertencem ao Observatory:

as regras em si (pertencem ao Nucleus);

a decisão sobre o que é violação (pertence ao Nucleus);

correção do código observado;

estado de execução da aplicação.

O Observatory **não** decide: ele relata.

### 4. Dependência

A direção conceitual é:

OBSERVATORY ──────► NUCLEUS

O inverso não deve ocorrer:

NUCLEUS ──X──► OBSERVATORY

O Nucleus define as regras e não sabe quem as verifica.

### 5. Estrutura

```text
observatory/
├── audits/          testes e análises de auditoria (estrutural, Etapa 4, Etapa 5)
└── solar/           o comando de verificação
    ├── cli.py       despacho de comandos
    ├── audit.py     registro em Markdown
    ├── commands/    os comandos
    └── check/       as auditorias geradas (Markdown)
```

### 6. Como verificar

```bash
python observatory/solar check              # verifica o diretório atual
python observatory/solar check <caminho>    # verifica outro projeto
```

A saída mostra o status de **cada** verificação — `correct` ou `violation` —
e, havendo violação, o detalhe de cada regra descoberta:

```text
SOLAR — verificação arquitetural

Dependency                violation
HttpInput                 correct
PlanetStructure           violation
...

resultado: violation — 8 violação(ões) em 3 regra(s)
auditoria: observatory/solar/check/check-2026-10-05-143000.md
```

O código de saída acompanha: `0` para `correct`, `1` para `violation`
e `2` para caminho inválido ou comando desconhecido.

### 7. Auditoria

**Toda** verificação é registrada em Markdown dentro de
`observatory/solar/check/` — ao lado do comando que o produziu —, com o momento
da execução, a raiz verificada, o status de todas as verificações e o detalhe de
cada violação.

Registrar **sempre** (`correct` ou `violation`) é o que torna o arquivo uma
garantia: o registro da última execução prova que ela aconteceu e como
terminou. Se só a violação gerasse arquivo, "nenhum arquivo novo" seria ambíguo
— tanto pode significar "está tudo certo" quanto "ninguém rodou a verificação".

O nome carrega o momento e o resultado:

```text
check-2026-10-05-155458-violation.md
check-2026-10-05-162011-correct.md
```

Então o arquivo mais recente diz, **sem precisar abrir**, se a última
verificação passou. A ordenação por nome é a ordenação cronológica.

Duas execuções no mesmo segundo não se sobrescrevem (recebem um sufixo
numérico).

A hora é a de **São Paulo** (`America/Sao_Paulo`), não a do servidor: o registro
é lido por pessoas no Brasil. Sem a base IANA na imagem, o deslocamento fixo
`-03:00` é usado — São Paulo não tem horário de verão desde 2019.
