from __future__ import annotations

import argparse
import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any


# Classes.
class PyArg(ABC, argparse.ArgumentParser):
    """
    **PyArg** is an abstract class that uses `argparse.ArgumentParser` class that allows you to set up easily sub
    parsers/commands from a parent parser.

    Creates a class inhenrance from **PyArg**, set up all arguments in `setup_arguments` method, and then, you can
    re-use the same parser definition to build your complex structure of parser arguments and CLI commands.

    Usage:
    ```
    class Forms(PyArg):
        def setup_arguments(self):
            self.add_argument("--username", "-u")
            self.add_argument("--password", "-p")

    parser = Forms(name="Forms")
    arguments = parser.get_arguments()
    ```

    Extra commands that trigger a function:
    ```
    class Application(PyArg):
        def setup_arguments(self):
            ...

    class MakeDir(PyArg):
        @staticmethod
        def create_directory(location, name_list):
            for name in name_list:
                os.makedirs(os.path.join(location, name))

        def setup_arguments(self):
            self.add_argument("--location", "-l")
            self.add_argument("--name", "-n", type=str, nargs="+")

    class DeleteDir(PyArg):
        @staticmethod
        def delete_directory(path):
            shutil.rmtree(path)

        def setup_arguments(self):
            self.add_argument("--path", "-p")

    make_dir_parser = MakeDir(name="Make Directory")
    delete_dir_parser = DeleteDir(name="Delete Directory")

    app = Application(name="Directory Manager")
    app.add_command_parser(parser=make_dir_parser, script_entrypoint=MakeDir.create_directory)
    app.add_command_parser(parser=delete_dir_parser, script_entrypoint=DeleteDir.delete_directory)
    app.get_arguments()
    ```
    """

    # Special methods.
    def __init__(
        self, name: str, description: str | None = None, parents: Iterable[PyArg] | None = None, **kwargs: Any
    ) -> None:
        # Remove parameters.
        for to_remove in ("prog", "description", "parents", "conflict_handler"):
            kwargs.pop(to_remove, None)
        parents = [] if parents is None else parents
        super().__init__(prog=name, description=description, parents=parents, conflict_handler="resolve", **kwargs)

        # Attributes.
        self.__command_name: str = self.__get_program_name(name=name)

        # Set up extra sub parsers.
        self.__subparser: None | argparse._SubParsersAction[argparse.ArgumentParser] = None

        # Set up arguments.
        self.setup_arguments()

    # Properties.
    @property
    def command_name(self) -> str:
        return self.__command_name

    # Abstract methods.
    @abstractmethod
    def setup_arguments(self) -> None:
        """Main method used to define all parameters of the parser."""

    # Private methods.
    def __get_program_name(self, name: str) -> str:
        """Convert the parser name to a CLI command name."""
        name = name.lower()
        name = re.sub(pattern=r"\s+", repl="-", string=name.strip())
        return name

    # Methods.
    def add_command_parser(
        self, parser: PyArg, description: str | None = None, script_entrypoint: Callable[..., Any] | None = None
    ) -> None:
        """Add an extra parser to a parent **PyArg** class to be called by `name`."""
        if self.__subparser is None:
            self.__subparser = self.add_subparsers(
                dest="command", parser_class=argparse.ArgumentParser, help="Available commands."
            )
        subparser: argparse.ArgumentParser = self.__subparser.add_parser(
            parents=[parser], name=parser.command_name, description=description or parser.description, add_help=False
        )
        # Add script.
        if script_entrypoint:
            subparser.set_defaults(_entrypoint=script_entrypoint)

    def get_arguments(self) -> dict[str, Any]:
        """Get the CLI arguments."""
        args: dict[str, Any] = vars(self.parse_args())
        args.pop("command", None)
        _entrypoint: Callable[..., Any] | None = args.pop("_entrypoint", None)
        if _entrypoint:
            _entrypoint(**args)
        return args
