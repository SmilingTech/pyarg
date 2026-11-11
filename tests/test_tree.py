"""Tests for the tree view."""

from __future__ import annotations

import argparse
import re

import pytest

from pyarg import PyArg

ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Greet(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--name", "-n", required=True, help="Person to greet.")


class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")
        self.add_argument("--target", default="local")
        self.add_argument("--secret", help=argparse.SUPPRESS)


class App(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--run", "-r", action="store_true", help="Run it.")


def render(parser: PyArg, capsys: pytest.CaptureFixture[str]) -> list[str]:
    parser.tree()
    return ANSI.sub("", capsys.readouterr().out).splitlines()


def test_root_is_first_line(capsys: pytest.CaptureFixture[str]) -> None:
    lines = render(App(name="Application"), capsys)
    assert lines[0] == str(App(name="Application"))


def test_parser_without_children(capsys: pytest.CaptureFixture[str]) -> None:
    class Empty(PyArg):
        def setup_arguments(self) -> None:
            pass

    assert len(render(Empty(), capsys)) == 1


def test_help_argument_is_hidden(capsys: pytest.CaptureFixture[str]) -> None:
    assert not any("--help" in line for line in render(App(), capsys))


def test_argument_label(capsys: pytest.CaptureFixture[str]) -> None:
    lines = render(Greet(), capsys)
    assert lines[1].startswith("└── --name, -n")
    assert "Person to greet." in lines[1]
    assert "(required)" in lines[1]


def test_default_is_shown(capsys: pytest.CaptureFixture[str]) -> None:
    line = next(line for line in render(Common(), capsys) if "--target" in line)
    assert "default=local" in line


def test_suppressed_help_is_hidden(capsys: pytest.CaptureFixture[str]) -> None:
    line = next(line for line in render(Common(), capsys) if "--secret" in line)
    assert line.endswith("--secret")


def test_full_structure(capsys: pytest.CaptureFixture[str]) -> None:
    app = App(pyarg_groups=Common(pyarg_groups=Greet()))
    app.add_command_parser(Greet(name="Say Hi"))
    lines = render(app, capsys)
    assert lines[1].startswith("├── --run, -r")
    assert lines[2].startswith("├── [group] Common(")
    assert lines[3].startswith("│   ├── --verbose")
    assert lines[6].startswith("│   └── [group] Greet(")
    assert lines[7].startswith("│       └── --name")
    assert lines[8].startswith("└── [command] Greet(name=Say Hi")
    assert lines[9].startswith("    └── --name")
    assert len(lines) == 10


def test_order_follows_definition(capsys: pytest.CaptureFixture[str]) -> None:
    app = App(pyarg_groups=[Greet(), Common()])
    text = "\n".join(render(app, capsys))
    assert text.index("[group] Greet(") < text.index("[group] Common(")
