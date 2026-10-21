# SOLAR-ROF-007 — um Model por arquivo.
#
# Usa a MESMA convenção de reconhecimento das SOLAR-RED-005 e SOLAR-RED-006
# (lugar OU nome), para não existirem duas definições de "o que é um
# Model" no projeto.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.rules.scanner.module_classes import (
    DeclaredClass,
    ModuleClasses,
)


class ModelsMustLiveInTheirOwnFile(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-007

    Cada Model deve ficar no seu PRÓPRIO arquivo.

    Um arquivo com vários Models obriga quem lê a percorrer o
    arquivo inteiro para achar um deles, mistura históricos no
    mesmo `git blame` e transforma qualquer mudança em conflito
    de merge.

    É VIOLAÇÃO:

        orbits/database/models/entities.py

            class UserModel:        ❌
                ...

            class DocumentModel:    ❌
                ...

    Correto — um arquivo por Model, com o nome do arquivo
    acompanhando o nome do Model:

        orbits/database/models/user_model.py

            class UserModel:        ✅
                ...

        orbits/database/models/document_model.py

            class DocumentModel:    ✅
                ...

    O que conta como Model usa a MESMA convenção das regras
    SOLAR-RED-005 e SOLAR-RED-006 — o LUGAR ou o NOME:

        segmento  o módulo tem o segmento "models"
                  (orbits.database.models.*) — a camada de Models,
                  onde TODA classe conta;
        módulo    o módulo termina em "model"/"_model"
                  (planets.documents.document_model);
        classe    a classe termina em "Model"
                  (UserModel) ou é exatamente "Model".

    Arquivos e classes fora disso não interessam à regra: um
    arquivo com dois Resources ou dois DTOs não é violação.

    Classe aninhada conta como classe declarada no arquivo.

    O contexto desta regra é um ModuleClasses.
    """

    # Segmento que identifica a coleção de Models no caminho do
    # módulo (mesma constante da SOLAR-RED-005/SOLAR-RED-006).
    MODELS_SEGMENT = "models"

    # Sufixo do nome do MÓDULO (snake_case), como nas regras
    # SOLAR-RED-005/SOLAR-RED-006: `user_model`.
    MODEL_MODULE_SUFFIX = "_model"

    # Sufixo do NOME da classe. As regras SOLAR-RED-005/SOLAR-RED-006 usam `_model`
    # porque olham o nome do MÓDULO (snake_case); aqui o alvo
    # também é a CLASSE, que pela convenção do projeto é
    # PascalCase.
    MODEL_SUFFIX = "Model"

    # Quantos Models um arquivo pode declarar.
    MAX_MODELS_PER_FILE = 1

    def code(self) -> str:
        return rule_code(STRUCTURE, 7)

    def description(self) -> str:
        return "Cada Model deve ficar no seu próprio arquivo."

    def validate(self, module: ModuleClasses) -> None:

        models = self._models(module)

        # `<=` e não `== 1`: zero Model passa (o arquivo não é da
        # camada), um passa (é o caso correto), dois ou mais violam. A
        # comparação com a CONSTANTE deixa o limite em um lugar só.
        if len(models) <= self.MAX_MODELS_PER_FILE:
            return

        raise SolarException(
            self._build_message(module, models)
        )

    def _models(
        self,
        module: ModuleClasses
    ) -> tuple[DeclaredClass, ...]:
        """
        Classes do arquivo que são Models.
        """

        # `tuple` e não lista: o resultado vai direto para a mensagem,
        # que cita as classes na ordem do ARQUIVO (a ordem de
        # `module.classes`).
        return tuple(
            declared
            for declared in module.classes
            if self._is_model(declared.name, module.module)
        )

    def _is_model(self, name: str, module: str) -> bool:
        """
        Reconhece o Model pelo LUGAR ou pelo NOME.

        São três critérios, os MESMOS das regras SOLAR-RED-005 e
        SOLAR-RED-006, mais o nome da CLASSE:

            segmento  "models" no caminho do módulo — a camada de
                      Models (tudo ali é Model);
            módulo    o módulo termina em "model"/"_model"
                      (user_model);
            classe    a classe termina em "Model" (UserModel).

        Consequência assumida do primeiro critério: em
        `orbits/database/models/`, TODA classe conta. Se o arquivo
        declara duas coisas, uma delas não pertence à camada de
        Models — um schema ou DTO mora em Resource.
        """

        parts = module.split(".")

        # Critério 1 — o LUGAR: em `models/`, TODA classe é Model. A
        # consequência assumida é que um schema ou DTO declarado ali
        # também conta — e deveria morar em Resource.
        if self.MODELS_SEGMENT in parts:
            return True

        last = parts[-1]

        # Critério 2 — o nome do MÓDULO (`user_model`), em snake_case.
        if last == "model" or last.endswith(self.MODEL_MODULE_SUFFIX):
            return True

        # Critério 3 — o nome da CLASSE (`UserModel`), em PascalCase.
        # Os sufixos são diferentes porque as convenções de nome são
        # diferentes; os três critérios valem em qualquer combinação.
        return name == self.MODEL_SUFFIX or name.endswith(
            self.MODEL_SUFFIX
        )

    def _build_message(
        self,
        module: ModuleClasses,
        models: tuple[DeclaredClass, ...]
    ) -> str:

        # Nome E linha: a linha é o que `DeclaredClass` guardou a mais,
        # e citá-la deixa a mensagem clicável no terminal.
        declared = ", ".join(
            f"{model.name} (linha {model.line})"
            for model in models
        )

        return (
            f"{self.code()}: o arquivo '{module.file}' declara "
            f"{len(models)} Models: {declared}. "
            f"Cada Model deve ficar no seu próprio arquivo, com o "
            f"nome do arquivo acompanhando o nome do Model "
            f"(ex.: user_model.py)."
        )
