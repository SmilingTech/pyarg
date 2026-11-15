"""Tests for the `--tree` option."""

from __future__ import annotations

import re
from typing import Callable

import pytest

from pyarg import PyArg


class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")


class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u", required=True)


class App(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--run", "-r", action="store_true")


@pytest.fixture
def app() -> App:
    return App(pyarg_groups=Common(), pyarg_commands=Login())


def run_tree(parser: PyArg, capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]) -> list[str]:
    with pytest.raises(SystemExit) as error:
        parser.get_arguments()
    assert error.value.code == 0
    return ansi_re.sub("", capsys.readouterr().out).splitlines()


def test_tree_option_prints_tree_and_exits(
    app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]
) -> None:
    argv("--tree")
    lines = run_tree(app, capsys, ansi_re)
    assert lines[0] == str(app)
    assert "├── [group] Common" in lines
    assert "└── [command] Login [$ login]" in lines


def test_tree_option_matches_tree_method(
    app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]
) -> None:
    app.tree()
    expected = ansi_re.sub("", capsys.readouterr().out).splitlines()
    argv("--tree")
    assert run_tree(app, capsys, ansi_re) == expected


def test_tree_option_on_simple_parser(
    argv: Callable[..., None], capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]
) -> None:
    argv("--tree")
    lines = run_tree(Common(), capsys, ansi_re)
    assert lines == ["Common(name=Common, description=None)", "└── --verbose, -v ; type=bool"]


def test_tree_option_on_command_shows_command_tree(
    app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]
) -> None:
    argv("login", "--tree")
    lines = run_tree(app, capsys, ansi_re)
    assert lines[0] == "Login(name=Login, description=None)"
    assert lines[1].startswith("└── --username, -u")
    assert not any("--run" in line for line in lines)


def test_tree_option_skips_required_arguments(
    argv: Callable[..., None], capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]
) -> None:
    argv("--tree")
    assert run_tree(Login(), capsys, ansi_re)[0] == str(Login())


def test_group_does_not_override_parent_tree_option(
    app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str], ansi_re: re.Pattern[str]
) -> None:
    argv("--tree")
    assert run_tree(app, capsys, ansi_re)[0].startswith("App(")


def test_tree_option_is_listed_once_in_help(
    app: App, argv: Callable[..., None], capsys: pytest.CaptureFixture[str]
) -> None:
    argv("-h")
    with pytest.raises(SystemExit):
        app.get_arguments()
    output = capsys.readouterr().out
    assert output.count("Show the parser structure as a tree and exit.") == 1
    options, common = output.split("Common:")
    assert "--tree" in options
    assert "--tree" not in common


def test_tree_option_is_not_in_arguments(app: App, argv: Callable[..., None]) -> None:
    argv("-r")
    assert "tree" not in app.get_arguments().arguments


def test_tree_option_is_not_shown_in_tree(app: App, capsys: pytest.CaptureFixture[str]) -> None:
    app.tree()
    assert "--tree" not in capsys.readouterr().out
