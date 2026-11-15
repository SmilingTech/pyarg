"""Tests for the `pyarg` decorator."""

from __future__ import annotations

import re
from typing import Callable

import pytest

from pyarg import PyArg, pyarg

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def test_without_parentheses_returns_pyarg() -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        parser.add_argument("--username", "-u")

    assert isinstance(login, PyArg)


def test_with_parentheses_returns_pyarg() -> None:
    @pyarg()
    def login(parser: PyArg) -> None:
        parser.add_argument("--username", "-u")

    assert isinstance(login, PyArg)


def test_class_is_named_after_function() -> None:
    @pyarg
    def make_directory(parser: PyArg) -> None:
        pass

    assert type(make_directory).__name__ == "MakeDirectory"


def test_name_and_command_name_from_function() -> None:
    @pyarg
    def make_directory(parser: PyArg) -> None:
        pass

    assert make_directory.name == "Make Directory"
    assert make_directory.command_name == "make-directory"


def test_explicit_name() -> None:
    @pyarg(name="Sign In")
    def login(parser: PyArg) -> None:
        pass

    assert login.name == "Sign In"
    assert login.command_name == "sign-in"


def test_description_from_docstring() -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        """Sign in.

        Uses the username and password.
        """

    assert login.description == "Sign in.\n\nUses the username and password."


def test_explicit_description_wins_over_docstring() -> None:
    @pyarg(description="Explicit.")
    def login(parser: PyArg) -> None:
        """Docstring."""

    assert login.description == "Explicit."


def test_without_description() -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        pass

    assert login.description is None


def test_function_receives_the_parser() -> None:
    received: list[PyArg] = []

    @pyarg
    def login(parser: PyArg) -> None:
        received.append(parser)

    assert received == [login]


def test_get_arguments(argv: Callable[..., None]) -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        parser.add_argument("--username", "-u")
        parser.add_argument("--port", type=int, default=80)

    argv("-u", "ana")
    output = login.get_arguments()
    assert output.command is None
    assert output.arguments == {"username": "ana", "port": 80}


def test_kwargs_are_forwarded() -> None:
    @pyarg(add_help=False)
    def login(parser: PyArg) -> None:
        pass

    assert not any(action.dest == "help" for action in login._actions)


def test_as_group(argv: Callable[..., None]) -> None:
    @pyarg
    def common(parser: PyArg) -> None:
        parser.add_argument("--verbose", "-v", action="store_true")

    @pyarg(pyarg_groups=common)
    def app(parser: PyArg) -> None:
        parser.add_argument("--run", "-r", action="store_true")

    argv("-v", "-r")
    assert app.get_arguments().arguments == {"run": True, "verbose": True}


def test_as_command(argv: Callable[..., None]) -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        parser.add_argument("--username", "-u")

    @pyarg(pyarg_commands=login)
    def app(parser: PyArg) -> None:
        pass

    argv("login", "-u", "ana")
    output = app.get_arguments()
    assert output.command == "login"
    assert output.arguments == {"username": "ana"}


def test_add_command_parser(argv: Callable[..., None]) -> None:
    @pyarg
    def items(parser: PyArg) -> None:
        parser.add_argument("--limit", type=int)

    @pyarg
    def projects(parser: PyArg) -> None:
        pass

    @pyarg
    def app(parser: PyArg) -> None:
        pass

    projects.add_command_parser(parser=items)
    app.add_command_parser(parser=projects)
    argv("projects", "items", "--limit", "5")
    assert app.get_arguments().arguments == {"limit": 5}


def test_entrypoint(argv: Callable[..., None]) -> None:
    @pyarg
    def greet(parser: PyArg) -> None:
        parser.add_argument("--name", "-n")

    greet.entrypoint = lambda name: f"Hello, {name}!"

    @pyarg(pyarg_commands=greet)
    def app(parser: PyArg) -> None:
        pass

    argv("greet", "-n", "ana")
    assert app.get_arguments().entrypoint_output == "Hello, ana!"


def test_mixed_with_class(argv: Callable[..., None]) -> None:
    class Login(PyArg):
        def setup_arguments(self) -> None:
            self.add_argument("--username", "-u")

    @pyarg(pyarg_commands=Login())
    def app(parser: PyArg) -> None:
        pass

    argv("login", "-u", "ana")
    assert app.get_arguments().command == "login"


def test_tree_shows_decorated_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        """Sign in."""
        parser.add_argument("--username", "-u", help="User.")

    @pyarg(pyarg_commands=login)
    def app(parser: PyArg) -> None:
        parser.add_argument("--run", "-r", action="store_true")

    app.tree()
    lines = ANSI.sub("", capsys.readouterr().out).splitlines()
    assert lines[1] == "├── --run, -r ; type=bool"
    assert lines[2] == "└── [command] Login [$ login] (Sign in.)"
    assert lines[3] == "    └── --username, -u ; type=str: User."


def test_tree_option(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    @pyarg
    def login(parser: PyArg) -> None:
        parser.add_argument("--username", "-u")

    argv("--tree")
    with pytest.raises(SystemExit) as error:
        login.get_arguments()
    assert error.value.code == 0
    assert "--username" in capsys.readouterr().out


def test_each_decorator_creates_its_own_class() -> None:
    @pyarg
    def first(parser: PyArg) -> None:
        parser.add_argument("--a")

    @pyarg
    def second(parser: PyArg) -> None:
        parser.add_argument("--b")

    assert type(first) is not type(second)
    assert {action.dest for action in first._actions} == {"help", "a", "tree"}
    assert {action.dest for action in second._actions} == {"help", "b", "tree"}
