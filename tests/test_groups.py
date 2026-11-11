"""Tests for `pyarg_groups`."""

from __future__ import annotations

from typing import Callable

import pytest

from pyarg import PyArg


class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true", help="Verbose output.")


class Auth(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u", required=True)
        self.add_argument("--password", "-p", default="secret")


class Output(PyArg):
    """Optional mutually exclusive group."""

    def setup_arguments(self) -> None:
        group = self.add_mutually_exclusive_group()
        group.add_argument("--json", action="store_true")
        group.add_argument("--yaml", action="store_true")


class Mode(PyArg):
    """Required mutually exclusive group."""

    def setup_arguments(self) -> None:
        group = self.add_mutually_exclusive_group(required=True)
        group.add_argument("--fast", action="store_true")
        group.add_argument("--slow", action="store_true")


class Mixed(PyArg):
    """Regular and mutually exclusive arguments together."""

    def setup_arguments(self) -> None:
        self.add_argument("--name")
        group = self.add_mutually_exclusive_group()
        group.add_argument("--a", action="store_true")
        group.add_argument("--b", action="store_true")


class App(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--debug", action="store_true")


# Basics.
def test_single_group(argv: Callable[..., None]) -> None:
    argv("-v", "--debug")
    output = App(name="App", pyarg_groups=Common(name="Common")).get_arguments()
    assert output.arguments == {"debug": True, "verbose": True}


def test_iterable_of_groups(argv: Callable[..., None]) -> None:
    argv("-v", "-u", "ana")
    output = App(name="App", pyarg_groups=[Common(name="Common"), Auth(name="Auth")]).get_arguments()
    assert output.arguments == {"debug": False, "verbose": True, "username": "ana", "password": "secret"}


def test_generator_of_groups(argv: Callable[..., None]) -> None:
    argv("-v")
    groups = (group for group in (Common(name="Common"),))
    assert App(name="App", pyarg_groups=groups).get_arguments().arguments["verbose"] is True


def test_no_groups(argv: Callable[..., None]) -> None:
    argv()
    assert App(name="App", pyarg_groups=None).get_arguments().arguments == {"debug": False}
    assert App(name="App", pyarg_groups=[]).get_arguments().arguments == {"debug": False}


def test_group_with_help_does_not_conflict() -> None:
    App(name="App", pyarg_groups=[Common(name="Common"), Auth(name="Auth")])


def test_help_is_defined_only_once() -> None:
    parser = App(name="App", pyarg_groups=[Common(name="Common"), Auth(name="Auth")])
    assert sum(1 for action in parser._actions if action.dest == "help") == 1


def test_group_with_add_help_false(argv: Callable[..., None]) -> None:
    argv("-v")
    output = App(name="App", pyarg_groups=Common(name="Common", add_help=False)).get_arguments()
    assert output.arguments["verbose"] is True


# Defaults and required.
def test_group_defaults(argv: Callable[..., None]) -> None:
    argv("-u", "ana")
    output = App(name="App", pyarg_groups=Auth(name="Auth")).get_arguments()
    assert output.arguments["password"] == "secret"


def test_group_required_argument_is_enforced(argv: Callable[..., None]) -> None:
    argv()
    with pytest.raises(SystemExit) as error:
        App(name="App", pyarg_groups=Auth(name="Auth")).get_arguments()
    assert error.value.code == 2


# Help output.
def test_help_shows_group_title_and_description(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    app = App(name="App", pyarg_groups=Common(name="Common", description="Shared options."))
    with pytest.raises(SystemExit) as error:
        app.get_arguments()
    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "Common:" in output
    assert "Shared options." in output
    assert "--verbose" in output


def test_help_shows_one_section_per_group(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    app = App(name="App", pyarg_groups=[Common(name="Common"), Auth(name="Auth")])
    with pytest.raises(SystemExit):
        app.get_arguments()
    output = capsys.readouterr().out
    assert "Common:" in output
    assert "Auth:" in output


def test_help_option_is_listed_once(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    app = App(name="App", pyarg_groups=[Common(name="Common"), Auth(name="Auth")])
    with pytest.raises(SystemExit):
        app.get_arguments()
    assert capsys.readouterr().out.count("show this help message") == 1


def test_help_places_group_arguments_under_their_section(
    argv: Callable[..., None], capsys: pytest.CaptureFixture[str]
) -> None:
    argv("-h")
    app = App(name="App", pyarg_groups=Common(name="Common"))
    with pytest.raises(SystemExit):
        app.get_arguments()
    output = capsys.readouterr().out
    options, group = output.split("\n\n", 1)[1].split("Common:")
    assert "--debug" in options
    assert "--verbose" not in options
    assert "--verbose" in group


# Mutually exclusive groups.
@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), {"json": False, "yaml": False}),
        (("--json",), {"json": True, "yaml": False}),
        (("--yaml",), {"json": False, "yaml": True}),
    ],
)
def test_optional_mutually_exclusive_group(
    args: tuple[str, ...], expected: dict[str, bool], argv: Callable[..., None]
) -> None:
    argv(*args)
    output = App(name="App", pyarg_groups=Output(name="Output")).get_arguments()
    assert {key: output.arguments[key] for key in expected} == expected


def test_optional_mutually_exclusive_group_conflict(argv: Callable[..., None]) -> None:
    argv("--json", "--yaml")
    with pytest.raises(SystemExit) as error:
        App(name="App", pyarg_groups=Output(name="Output")).get_arguments()
    assert error.value.code == 2


def test_required_mutually_exclusive_group(argv: Callable[..., None]) -> None:
    argv("--fast")
    output = App(name="App", pyarg_groups=Mode(name="Mode")).get_arguments()
    assert output.arguments["fast"] is True
    assert output.arguments["slow"] is False


def test_required_mutually_exclusive_group_missing(argv: Callable[..., None]) -> None:
    argv()
    with pytest.raises(SystemExit) as error:
        App(name="App", pyarg_groups=Mode(name="Mode")).get_arguments()
    assert error.value.code == 2


def test_required_mutually_exclusive_group_conflict(argv: Callable[..., None]) -> None:
    argv("--fast", "--slow")
    with pytest.raises(SystemExit) as error:
        App(name="App", pyarg_groups=Mode(name="Mode")).get_arguments()
    assert error.value.code == 2


def test_mutually_exclusive_flags_are_kept(argv: Callable[..., None]) -> None:
    parser = App(name="App", pyarg_groups=[Output(name="Output"), Mode(name="Mode")])
    assert len(parser._mutually_exclusive_groups) == 2
    assert sorted(group.required for group in parser._mutually_exclusive_groups) == [False, True]


def test_mixed_regular_and_exclusive_arguments(argv: Callable[..., None]) -> None:
    argv("--name", "x", "--a")
    output = App(name="App", pyarg_groups=Mixed(name="Mixed")).get_arguments()
    assert output.arguments == {"debug": False, "name": "x", "a": True, "b": False}


def test_mixed_exclusive_conflict_only_between_exclusive(argv: Callable[..., None]) -> None:
    argv("--name", "x", "--a", "--b")
    with pytest.raises(SystemExit) as error:
        App(name="App", pyarg_groups=Mixed(name="Mixed")).get_arguments()
    assert error.value.code == 2


def test_exclusive_group_usage_in_help(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    argv("-h")
    with pytest.raises(SystemExit):
        App(name="App", pyarg_groups=Mode(name="Mode")).get_arguments()
    assert "--fast | --slow" in capsys.readouterr().out


# Reuse.
def test_same_group_instance_in_two_parsers(argv: Callable[..., None]) -> None:
    common = Common(name="Common")
    first = App(name="First", pyarg_groups=common)
    second = Auth(name="Second", pyarg_groups=common)
    argv("-v")
    assert first.get_arguments().arguments["verbose"] is True
    argv("-v", "-u", "ana")
    assert second.get_arguments().arguments["verbose"] is True


def test_group_does_not_change_source_parser() -> None:
    mode = Mode(name="Mode")
    before = list(mode._actions)
    App(name="App", pyarg_groups=mode)
    assert mode._actions == before
    assert len(mode._mutually_exclusive_groups) == 1


# Groups with commands.
def test_group_with_sub_command(argv: Callable[..., None]) -> None:
    app = App(name="App")
    app.add_command_parser(Auth(name="Login", pyarg_groups=[Common(name="Common"), Output(name="Output")]))
    argv("login", "-u", "ana", "-v", "--json")
    output = app.get_arguments()
    assert output.command == "login"
    assert output.arguments == {
        "debug": False,
        "username": "ana",
        "password": "secret",
        "verbose": True,
        "json": True,
        "yaml": False,
    }


def test_group_in_command_help(argv: Callable[..., None], capsys: pytest.CaptureFixture[str]) -> None:
    app = App(name="App")
    app.add_command_parser(Auth(name="Login", pyarg_groups=Common(name="Common")))
    argv("login", "-h")
    with pytest.raises(SystemExit) as error:
        app.get_arguments()
    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "Common:" in output
    assert "--verbose" in output


def test_group_on_parent_and_command(argv: Callable[..., None]) -> None:
    app = App(name="App", pyarg_groups=Common(name="Common"))
    app.add_command_parser(Auth(name="Login"))
    argv("-v", "login", "-u", "ana")
    output = app.get_arguments()
    assert output.command == "login"
    assert output.arguments["verbose"] is True
    assert output.arguments["username"] == "ana"


# Native argparse behavior.
def test_native_parents_still_work(argv: Callable[..., None]) -> None:
    argv("-v")
    output = App(name="App", parents=[Common(name="Common", add_help=False)]).get_arguments()
    assert output.arguments["verbose"] is True
