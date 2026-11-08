# PyArg

A small layer on top of `argparse` to build CLIs with sub-commands by **reusing parser classes**.

Each parser is a class. You define its arguments in one method, and then plug that class into another parser as a
command, without rewriting the arguments.

## Installation

```bash
pip install .
```

For development (changes apply without reinstalling):

```bash
pip install -e .
```

Requires Python 3.10+ and has no dependencies.

## Quick start

Create a class that inherits from `PyArg` and define the arguments in `setup_arguments`:

```python
from pyarg import PyArg


class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u")
        self.add_argument("--password", "-p")


parser = Login(name="Login")
print(parser.get_arguments())
```

```console
$ python main.py -u ana -p 123
{'username': 'ana', 'password': '123'}
```

Since `PyArg` inherits from `argparse.ArgumentParser`, everything from `argparse` still works
(`add_argument`, `add_mutually_exclusive_group`, `type`, `nargs`, `choices`, etc.).

## Sub-commands

Use `add_command_parser` to attach parsers to a main one. Each command is named after the parser `name`, converted to
lowercase with spaces replaced by `-` (`"Make Directory"` becomes `make-directory`).

```python
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
        pass  # The main parser can have its own arguments too.


app = App(name="My App", description="Demo app.")
app.add_command_parser(Login(name="Login", description="Sign in."))
app.add_command_parser(Logout(name="Logout"), description="Sign out.")

print(app.get_arguments())
```

```console
$ python main.py login -u ana -p 123
{'command': 'login', 'username': 'ana', 'password': '123'}

$ python main.py logout --all
{'command': 'logout', 'all': True}

$ python main.py -h
usage: My App [-h] {login,logout} ...
```

The chosen command is available under the `command` key.

## Reusing arguments

Arguments from other parsers can be inherited with `parents`:

```python
class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")


class Build(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--target")


build = Build(name="Build", parents=[Common(name="Common", add_help=False)])
```

Use `add_help=False` on the parent parser so the `-h` option is not registered twice.

## API

### `PyArg(name, description=None, parents=[], **kwargs)`

Abstract class. It cannot be instantiated directly, you must inherit from it and implement `setup_arguments`.

- `name`: parser name. Used as `prog` in the help text and to build the command name.
- `description`: text shown in `-h`.
- `parents`: other parsers whose arguments are copied into this one.
- `**kwargs`: forwarded to `argparse.ArgumentParser`. The `prog`, `description`, `parents` and `conflict_handler`
  keys are ignored, as `conflict_handler` is always `"resolve"`.

### `setup_arguments(self) -> None`

Abstract method. Define all the arguments of the parser here. It runs at the end of `__init__`.

### `command_name`

Read-only property with the command name derived from `name`.

### `add_command_parser(parser, description=None, script_entrypoint=None)`

Adds `parser` as a sub-command. If `description` is not set, the parser's own description is used.

`script_entrypoint` stores a callable on the command, but `get_arguments` does not call it and removes it from the
result.

### `get_arguments() -> dict[str, Any]`

Parses `sys.argv` and returns the arguments passed by the user as a dictionary.

## Development

See [DEVELOPERS.md](DEVELOPERS.md).
