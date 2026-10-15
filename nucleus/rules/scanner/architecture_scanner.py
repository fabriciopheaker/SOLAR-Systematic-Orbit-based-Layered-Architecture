import ast
from pathlib import Path

from nucleus.rules.scanner.dependency import Dependency
from nucleus.rules.scanner.source_files import source_files


class ArchitectureScanner:
    """
    Scanner responsável por analisar o código-fonte da aplicação
    e identificar as dependências existentes entre seus módulos.

    O Scanner é uma camada de análise da arquitetura e NÃO é
    responsável por decidir se uma dependência é permitida ou não.

    Sua responsabilidade é responder apenas:

        "Quem depende de quem?"

    A validação das regras arquiteturais é responsabilidade do
    RuleEngine e das Rules.

    Exemplo:

        planets/user/repository.py

            from planets.auth.repository import AuthRepository

    O Scanner produzirá uma Dependency equivalente a:

        source = "planets.user.repository"
        target = "planets.auth.repository"

    Dessa forma, as Rules podem trabalhar sobre a estrutura
    arquitetural sem precisar conhecer o conteúdo dos arquivos.
    """

    def __init__(self, root: Path):
        """
        Inicializa o Scanner.

        Args:
            root:
                Diretório raiz do projeto que será analisado.

        A raiz deve representar o projeto SOLAR, e não a raiz
        do sistema operacional.

        Exemplo:

            PROJECT_ROOT/
            ├── nucleus/
            ├── atmosphere/
            ├── orbits/
            ├── planets/
            └── satellites/
        """

        self.root = root.resolve()

    def scan(self) -> list[Dependency]:
        """
        Analisa todo o projeto e retorna as dependências encontradas.

        O método percorre todos os arquivos Python existentes dentro
        da raiz do projeto e delega a análise individual de cada arquivo
        para o método `_scan_file()`.

        Returns:
            list[Dependency]:
                Lista contendo todas as dependências identificadas
                durante a análise.
        """

        dependencies: list[Dependency] = []

        # Percorre recursivamente todos os arquivos Python
        # existentes dentro da raiz do projeto.
        for file in source_files(self.root):

            # Analisa o arquivo e adiciona suas dependências
            # à coleção geral do Scanner.
            dependencies.extend(
                self._scan_file(file)
            )

        return dependencies

    def _scan_file(self, file: Path) -> list[Dependency]:
        """
        Analisa um único arquivo Python.

        O código-fonte é convertido para uma árvore sintática
        utilizando o módulo `ast` do Python.

        O código NÃO é executado durante essa análise.

        São identificados dois tipos principais de import:

            import modulo

        e:

            from modulo import Classe

        Args:
            file:
                Caminho absoluto do arquivo Python analisado.

        Returns:
            list[Dependency]:
                Dependências encontradas no arquivo.
        """

        # Lê o conteúdo do arquivo como texto.
        source_code = file.read_text(
            encoding="utf-8"
        )

        # Converte o código-fonte em uma Abstract Syntax Tree (AST).
        #
        # A AST permite analisar a estrutura do código sem executá-lo.
        #
        # Isso é importante para o Linter porque queremos analisar
        # a arquitetura da aplicação de maneira segura.
        tree = ast.parse(
            source_code,
            filename=str(file)
        )

        # Converte o caminho do arquivo para o formato de módulo Python.
        #
        # Exemplo:
        #
        #   planets/user/repository.py
        #
        # torna-se:
        #
        #   planets.user.repository
        #
        source = self._module_name(file)

        dependencies: list[Dependency] = []

        # Percorre todos os nós existentes na AST.
        for node in ast.walk(tree):

            # Trata:
            #
            #   import planets.auth.repository
            #
            if isinstance(node, ast.Import):

                for alias in node.names:

                    dependencies.append(
                        Dependency(
                            source=source,
                            target=alias.name,
                            file=self._relative_file(file),
                            line=node.lineno
                        )
                    )

            # Trata:
            #
            #   from planets.auth.repository import AuthRepository
            #
            elif isinstance(node, ast.ImportFrom):

                # Alguns imports podem não possuir um módulo explícito.
                #
                # Exemplo:
                #
                #   from . import alguma_coisa
                #
                # Nesse primeiro estágio, esses casos serão tratados
                # posteriormente pelo resolvedor de imports relativos.
                if node.module is None:
                    continue

                target = self._resolve_import(
                    source,
                    node
                )

                dependencies.append(
                    Dependency(
                        source=source,
                        target=target,
                        file=self._relative_file(file),
                        line=node.lineno
                    )
                )

        return dependencies

    def _resolve_import(
        self,
        source: str,
        node: ast.ImportFrom
    ) -> str:
        """
        Resolve um import encontrado em um `from ... import ...`.

        O Python possui dois tipos de import que precisamos
        considerar:

        Import absoluto:

            from planets.auth import AuthRepository

        Import relativo:

            from ..auth import AuthRepository

        Imports absolutos podem ser utilizados diretamente.

        Imports relativos precisam ser convertidos para uma
        representação absoluta para que o RuleEngine trabalhe
        sempre com o mesmo formato.

        Args:
            source:
                Módulo onde o import foi encontrado.

            node:
                Nó AST correspondente ao ImportFrom.

        Returns:
            str:
                Caminho do módulo importado.
        """

        # Import absoluto.
        #
        # Exemplo:
        #
        # from planets.auth import AuthRepository
        #
        if node.level == 0:
            return node.module

        # Determina o pacote onde o módulo de origem está localizado.
        source_parts = source.split(".")

        # O arquivo Python é considerado um módulo.
        #
        # Exemplo:
        #
        # planets.user.repository
        #
        # O pacote do módulo é:
        #
        # planets.user
        package_parts = source_parts[:-1]

        # Cada nível de "." em um import relativo representa
        # uma subida na hierarquia de pacotes.
        #
        # level=1:
        #
        #   from .auth import ...
        #
        # level=2:
        #
        #   from ..auth import ...
        #
        # Portanto removemos `level - 1` níveis do pacote atual.
        if node.level > len(package_parts) + 1:
            raise ValueError(
                f"Import relativo inválido no módulo '{source}'."
            )

        package_parts = package_parts[
            :len(package_parts) - (node.level - 1)
        ]

        if node.module:
            package_parts.append(node.module)

        return ".".join(package_parts)

    def _module_name(self, file: Path) -> str:
        """
        Converte o caminho de um arquivo Python em seu nome de módulo.

        Exemplo:

            PROJECT_ROOT/
                planets/
                    user/
                        repository.py

        Resultado:

            planets.user.repository

        O caminho absoluto do computador nunca faz parte do resultado.
        """

        relative = file.relative_to(self.root)

        return ".".join(
            relative.with_suffix("").parts
        )

    def _relative_file(self, file: Path) -> str:
        """
        Retorna o caminho do arquivo relativo à raiz do projeto.

        Isso evita armazenar caminhos absolutos da máquina no resultado
        do Scanner.

        Exemplo:

            /home/user/projeto/planets/user/repository.py

        torna-se:

            planets/user/repository.py
        """

        return file.relative_to(self.root).as_posix()