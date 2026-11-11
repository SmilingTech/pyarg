"""Tests for parsing arguments with `get_arguments`."""

from __future__ import annotations

from typing import Callable

import pytest

from pyarg import PyArg


class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u")
        self.add_argument("--password", "-p")


class Flags(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--all", action="store_true")
        self.add_argument("--count", "-c", type=int, default=1)


class Required(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--token", required=True)


class Empty(PyArg):
    def setup_arguments(self) -> None:
        pass


def test_without_args(argv: Callable[..., None]) -> None:
    argv()
    assert Empty(name="App").get_arguments().arguments == {}


def test_simple_parser(argv: Callable[..., None]) -> None:
    argv("-u", "ana", "--password", "123")
    output = Login(name="Login").get_arguments()
    assert output.command is None
    assert output.arguments == {"username": "ana", "password": "123"}
    assert output.entrypoint_output is None


def test_missing_values_are_none(argv: Callable[..., None]) -> None:
    argv()
    assert Login(name="Login").get_arguments().arguments == {"username": None, "password": None}


def test_defaults_and_types(argv: Callable[..., None]) -> None:
    argv()
    assert Flags(name="Flags").get_arguments().arguments == {"all": False, "count": 1}
    argv("--all", "-c", "5")
    assert Flags(name="Flags").get_arguments().arguments == {"all": True, "count": 5}


def test_invalid_type_exits(argv: Callable[..., None]) -> None:
    argv("-c", "abc")
    with pytest.raises(SystemExit) as error:
        Flags(name="Flags").get_arguments()
    assert error.value.code == 2


def test_unknown_argument_exits(argv: Callable[..., None]) -> None:
    argv("--nope")
    with pytest.raises(SystemExit) as error:
        Login(name="Login").get_arguments()
    assert error.value.code == 2


def test_missing_required_argument_exits(argv: Callable[..., None]) -> None:
    argv()
    with pytest.raises(SystemExit) as error:
        Required(name="Required").get_arguments()
    assert error.value.code == 2


def test_help_exits_with_zero(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    with pytest.raises(SystemExit) as error:
        Login(name="Login", description="Sign in.").get_arguments()
    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "--username" in output
    assert "Sign in." in output
