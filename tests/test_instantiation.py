"""Tests for creating PyArg classes."""

from __future__ import annotations

from typing import Callable

import pytest

from pyarg import PyArg


class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u")
        self.add_argument("--password", "-p")


def test_cannot_instantiate_abstract_class() -> None:
    with pytest.raises(TypeError):
        PyArg(name="Abstract")  # type: ignore[abstract]


def test_setup_arguments_is_called_on_init() -> None:
    parser = Login(name="Login")
    destinations = {action.dest for action in parser._actions}
    assert {"username", "password"} <= destinations


def test_name_is_stripped() -> None:
    assert Login(name="  Login  ").name == "Login"


def test_description() -> None:
    assert Login(name="Login", description="Sign in.").description == "Sign in."


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


def test_native_kwargs_are_forwarded() -> None:
    parser = Login(name="Login", add_help=False)
    assert not any(action.dest == "help" for action in parser._actions)


def test_name_defaults_to_class_name() -> None:
    parser = Login()
    assert parser.name == "Login"
    assert parser.prog == "Login"
    assert parser.command_name == "login"


def test_explicit_name_overrides_class_name() -> None:
    assert Login(name="Sign In").name == "Sign In"


def test_command_without_name_uses_class_name(argv: Callable[..., None]) -> None:
    class App(PyArg):
        def setup_arguments(self) -> None:
            pass

    app = App()
    app.add_command_parser(Login())
    argv("login", "-u", "ana")
    assert app.get_arguments().command == "login"
