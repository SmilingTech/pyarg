"""Tests for running a function per command."""

from __future__ import annotations

from typing import Any, Callable

import pytest

from pyarg import PyArg


class SumNumber(PyArg):
    @staticmethod
    def sum_number(number: int) -> int:
        return number + 10

    def setup_arguments(self) -> None:
        self.add_argument("--number", "-n", type=int)


class Logout(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--all", action="store_true")


class App(PyArg):
    def setup_arguments(self) -> None:
        pass


@pytest.fixture
def app() -> App:
    app = App(name="My App")
    app.add_command_parser(SumNumber(name="Sum number to ten"), script_entrypoint=SumNumber.sum_number)
    return app


@pytest.mark.parametrize("number", [5, 10, 20])
def test_entrypoint_output(number: int, app: App, argv: Callable[..., None]) -> None:
    argv("sum-number-to-ten", "-n", str(number))
    output = app.get_arguments()
    assert output.command == "sum-number-to-ten"
    assert output.arguments == {"number": number}
    assert output.entrypoint_output == number + 10


def test_entrypoint_receives_arguments_without_command(argv: Callable[..., None]) -> None:
    received: dict[str, Any] = {}

    def entrypoint(**kwargs: Any) -> None:
        received.update(kwargs)

    app = App(name="App")
    app.add_command_parser(Logout(name="Logout"), script_entrypoint=entrypoint)
    argv("logout", "--all")
    app.get_arguments()
    assert received == {"all": True}


def test_entrypoint_returning_none(argv: Callable[..., None]) -> None:
    app = App(name="App")
    app.add_command_parser(Logout(name="Logout"), script_entrypoint=lambda **_: None)
    argv("logout")
    output = app.get_arguments()
    assert output.command == "logout"
    assert output.arguments == {"all": False}
    assert output.entrypoint_output is None


def test_entrypoint_is_called_once(argv: Callable[..., None]) -> None:
    calls: list[int] = []
    app = App(name="App")
    app.add_command_parser(Logout(name="Logout"), script_entrypoint=lambda **_: calls.append(1))
    argv("logout")
    app.get_arguments()
    assert calls == [1]


def test_command_without_entrypoint(argv: Callable[..., None]) -> None:
    app = App(name="App")
    app.add_command_parser(Logout(name="Logout"))
    argv("logout")
    assert app.get_arguments().entrypoint_output is None


def test_entrypoints_are_per_command(argv: Callable[..., None]) -> None:
    app = App(name="App")
    app.add_command_parser(SumNumber(name="Sum"), script_entrypoint=SumNumber.sum_number)
    app.add_command_parser(Logout(name="Logout"))
    argv("logout")
    assert app.get_arguments().entrypoint_output is None
    argv("sum", "-n", "1")
    assert app.get_arguments().entrypoint_output == 11
