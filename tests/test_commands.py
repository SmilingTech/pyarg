"""Tests for sub-commands."""

from __future__ import annotations

from typing import Callable

import pytest

from pyarg import PyArg


class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u")
        self.add_argument("--password", "-p")


class Logout(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--all", action="store_true")


class App(PyArg):
    def setup_arguments(self) -> None:
        pass


@pytest.fixture
def app() -> App:
    app = App(name="My App", description="Test application.")
    app.add_command_parser(Login(name="Login", description="Sign in."))
    app.add_command_parser(Logout(name="Logout"), description="Sign out.")
    return app


def test_login(app: App, argv: Callable[..., None]) -> None:
    argv("login", "-u", "ana", "-p", "123")
    output = app.get_arguments()
    assert output.command == "login"
    assert output.arguments == {"username": "ana", "password": "123"}
    assert output.entrypoint_output is None


def test_logout(app: App, argv: Callable[..., None]) -> None:
    argv("logout", "--all")
    output = app.get_arguments()
    assert output.command == "logout"
    assert output.arguments == {"all": True}


def test_no_command_selected(app: App, argv: Callable[..., None]) -> None:
    argv()
    output = app.get_arguments()
    assert output.command is None
    assert output.arguments == {}


def test_unknown_command_exits(app: App, argv: Callable[..., None]) -> None:
    argv("signup")
    with pytest.raises(SystemExit) as error:
        app.get_arguments()
    assert error.value.code == 2


def test_command_argument_does_not_leak_to_other_command(app: App, argv: Callable[..., None]) -> None:
    argv("logout", "-u", "ana")
    with pytest.raises(SystemExit) as error:
        app.get_arguments()
    assert error.value.code == 2


def test_command_help_has_no_conflict(app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("login", "-h")
    with pytest.raises(SystemExit) as error:
        app.get_arguments()
    assert error.value.code == 0
    assert "--username" in capsys.readouterr().out


def test_main_help_lists_commands(app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    with pytest.raises(SystemExit):
        app.get_arguments()
    output = capsys.readouterr().out
    assert "login" in output
    assert "logout" in output


@pytest.mark.parametrize(("command", "description"), [("login", "Sign in."), ("logout", "Sign out.")])
def test_command_description(
    command: str, description: str, app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str]
) -> None:
    argv(command, "-h")
    with pytest.raises(SystemExit):
        app.get_arguments()
    assert description in capsys.readouterr().out


def test_commands_without_subparser_are_lazy() -> None:
    app = App(name="App")
    assert not any(isinstance(action.dest, str) and action.dest == "command" for action in app._actions)
