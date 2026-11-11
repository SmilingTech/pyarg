from __future__ import annotations

import argparse
import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator
from typing import Any

from pyarg.types import PyArgOutput


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
        self,
        name: str | None = None,
        description: str | None = None,
        pyarg_groups: PyArg | Iterable[PyArg] | None = None,
        **kwargs: Any,
    ) -> None:
        # Remove parameters.
        for to_remove in ("prog", "description", "conflict_handler"):
            kwargs.pop(to_remove, None)
        name = name if name is not None else type(self).__name__
        super().__init__(prog=name, description=description, conflict_handler="resolve", **kwargs)

        # Attributes.
        self.__name: str = name.strip()
        self.__command_name: str = self.__get_program_name()
        self.__groups: list[PyArg] = []
        self.__commands: list[PyArg] = []

        # Set up extra sub parsers.
        self.__subparser: None | argparse._SubParsersAction[argparse.ArgumentParser] = None

        # Set up arguments.
        self.setup_arguments()

        # Keep only the arguments defined by this parser (groups share `_actions`).
        self.__own_arguments: list[argparse.Action] = [
            action for action in self._actions if not isinstance(action, argparse._HelpAction)
        ]

        # Set up argument groups.
        if pyarg_groups:
            pyarg_groups = [pyarg_groups] if isinstance(pyarg_groups, PyArg) else pyarg_groups
            for pyarg in pyarg_groups:
                self.setup_group_arguments(pyarg=pyarg)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}(name={self.name}, description={self.description}, command_name={self.command_name})"
        )

    # Properties.
    @property
    def name(self) -> str:
        return self.__name

    @property
    def command_name(self) -> str:
        return self.__command_name

    # Abstract methods.
    @abstractmethod
    def setup_arguments(self) -> None:
        """Main method used to define all parameters of the parser."""

    # Private methods.
    def __get_program_name(self) -> str:
        """Convert the parser name to a CLI command name."""
        name = self.__name.lower()
        name = re.sub(pattern=r"\s+", repl="-", string=name)
        return name

    def __tree_lines(self, prefix: str) -> Iterator[str]:
        """Yield one line per child, recursing into groups and commands."""
        children: list[argparse.Action | PyArg] = [*self.__own_arguments, *self.__groups, *self.__commands]
        for idx, child in enumerate(children):
            is_last: bool = idx == len(children) - 1
            yield f"{prefix}{'└── ' if is_last else '├── '}{self.__tree_label(child)}"
            if isinstance(child, PyArg):
                yield from child.__tree_lines(prefix=prefix + ("    " if is_last else "│   "))

    def __tree_label(self, child: argparse.Action | PyArg) -> str:
        """Text shown for each node of the tree."""
        if isinstance(child, PyArg):
            kind: str = "\033[31mcommand\033[0m" if child in self.__commands else "\033[32mgroup\033[0m"
            return f"[{kind}] {child}"
        label: str = ", ".join(child.option_strings) or child.dest
        if child.default and child.default != argparse.SUPPRESS:
            label += f" ; default={child.default}"
        if child.help and child.help != argparse.SUPPRESS:
            label += f": {child.help}"
        if child.required:
            label += " (required)"
        return label

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
        self.__commands.append(parser)

        # Add script.
        if script_entrypoint:
            subparser.set_defaults(_entrypoint=script_entrypoint)

    def setup_group_arguments(self, pyarg: PyArg) -> None:
        """Include extra arguments to the main PyArg as groups."""
        parser_group: argparse._ArgumentGroup = self.add_argument_group(title=pyarg.name, description=pyarg.description)
        self.__groups.append(pyarg)

        # Get all mutually exclusive groups.
        mutually_exclusive: list[argparse._MutuallyExclusiveGroup] = pyarg._mutually_exclusive_groups
        exclusive_actions: set[int] = {id(action) for group in mutually_exclusive for action in group._group_actions}

        # Add actions.
        for action in pyarg._actions:
            if isinstance(action, argparse._HelpAction) or id(action) in exclusive_actions:
                continue
            parser_group._add_action(action=action)

        # Set up again all mutually exclusive groups.
        for group in mutually_exclusive:
            new_group = parser_group.add_mutually_exclusive_group(required=group.required)
            for action in group._group_actions:
                new_group._add_action(action=action)

    def get_arguments(self) -> PyArgOutput:
        """Get the CLI arguments."""
        args: dict[str, Any] = vars(self.parse_args())
        command: str | None = args.pop("command", None)
        _entrypoint: Callable[..., Any] | None = args.pop("_entrypoint", None)
        entrypoint_output: Any | None = _entrypoint(**args) if _entrypoint else None
        return PyArgOutput(command=command, arguments=args, entrypoint_output=entrypoint_output)

    def tree(self) -> None:
        """Return the parser structure (arguments, groups and commands) as a tree."""
        print("\n".join([str(self), *self.__tree_lines(prefix="")]))
