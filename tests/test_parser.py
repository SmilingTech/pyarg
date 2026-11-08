"""Tests for the PyArg class."""

from __future__ import annotations

import sys
from typing import Any

import pytest

from pyarg import PyArg


# Helpers.
class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u")
        self.add_argument("--password", "-p")


class Logout(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--all", action="store_true")


class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")


class App(PyArg):
    def setup_arguments(self) -> None:
        pass


@pytest.fixture
def argv(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Set `sys.argv` as if the CLI had been called with the given arguments."""

    def _set(*args: str) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", *args])

    return _set


@pytest.fixture
def app() -> App:
    app = App(name="My App", description="Test application.")
    app.add_command_parser(Login(name="Login", description="Sign in."))
    app.add_command_parser(Logout(name="Logout"), description="Sign out.")
    return app


# Instantiation.
def test_cannot_instantiate_abstract_class() -> None:
    with pytest.raises(TypeError):
        PyArg(name="Abstract")  # type: ignore[abstract]


def test_setup_arguments_is_called_on_init() -> None:
    parser = Login(name="Login")
    destinations = {action.dest for action in parser._actions}
    assert {"username", "password"} <= destinations


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Login", "login"),
        ("Make Directory", "make-directory"),
        ("  Spaced   Out  ", "spaced-out"),
    ],
)
def test_command_name(name: str, expected: str) -> None:
    assert Login(name=name).command_name == expected


def test_reserved_kwargs_are_ignored() -> None:
    parser = Login(name="Login", prog="other", conflict_handler="error")
    assert parser.prog == "Login"
    assert parser.conflict_handler == "resolve"


# Parsing.
def test_get_arguments_without_args(argv: Any) -> None:
    argv()
    assert App(name="App").get_arguments() == {}


def test_get_arguments_simple_parser(argv: Any) -> None:
    argv("-u", "ana", "--password", "123")
    assert Login(name="Login").get_arguments() == {"username": "ana", "password": "123"}


def test_unknown_argument_exits(argv: Any) -> None:
    argv("--nope")
    with pytest.raises(SystemExit) as error:
        Login(name="Login").get_arguments()
    assert error.value.code == 2


# Sub-commands.
def test_command_login(app: App, argv: Any) -> None:
    argv("login", "-u", "ana", "-p", "123")
    assert app.get_arguments() == {"command": "login", "username": "ana", "password": "123"}


def test_command_logout(app: App, argv: Any) -> None:
    argv("logout", "--all")
    assert app.get_arguments() == {"command": "logout", "all": True}


def test_no_command_selected(app: App, argv: Any) -> None:
    argv()
    assert app.get_arguments() == {"command": None}


def test_unknown_command_exits(app: App, argv: Any) -> None:
    argv("signup")
    with pytest.raises(SystemExit):
        app.get_arguments()


def test_command_help_has_no_conflict(app: App, argv: Any, capsys: pytest.CaptureFixture[str]) -> None:
    argv("login", "-h")
    with pytest.raises(SystemExit) as error:
        app.get_arguments()
    assert error.value.code == 0
    assert "--username" in capsys.readouterr().out


def test_main_help_lists_commands(app: App, argv: Any, capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    with pytest.raises(SystemExit):
        app.get_arguments()
    output = capsys.readouterr().out
    assert "login" in output
    assert "logout" in output


def test_command_description(app: App, argv: Any, capsys: pytest.CaptureFixture[str]) -> None:
    for command, description in (("login", "Sign in."), ("logout", "Sign out.")):
        argv(command, "-h")
        with pytest.raises(SystemExit):
            app.get_arguments()
        assert description in capsys.readouterr().out


def test_entrypoint_is_not_returned(argv: Any) -> None:
    app = App(name="App")
    app.add_command_parser(Logout(name="Logout"), script_entrypoint=lambda **_: None)
    argv("logout")
    assert app.get_arguments() == {"command": "logout", "all": False}


# Parents.
def test_parents_reuse_arguments(argv: Any) -> None:
    parser = Login(name="Login", parents=[Common(name="Common", add_help=False)])
    argv("-v", "-u", "ana")
    assert parser.get_arguments() == {"verbose": True, "username": "ana", "password": None}


def test_parents_with_help_do_not_conflict() -> None:
    Login(name="Login", parents=[Common(name="Common")])
