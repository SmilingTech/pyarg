# PyArg

A small layer on top of `argparse` to build CLIs with sub-commands by **reusing parser classes**.

Each parser is a class. You define its arguments in one method, and then plug that class into another parser as a
command, without rewriting the arguments.

## Installation

```bash
pip install py-arguments
```

## Quick start

Create a class that inherits from `PyArg` and define the arguments in `setup_arguments`:

```python
from pyarg import PyArg


class Login(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--username", "-u")
        self.add_argument("--password", "-p")


parser = Login(name="Login")
output = parser.get_arguments()
print(output.arguments)
```

```console
$ python main.py -u ana -p 123
{'username': 'ana', 'password': '123'}
```

`get_arguments` returns a [`PyArgOutput`](#pyargoutput) with the parsed arguments and some extra information.

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

output = app.get_arguments()
print(output.command, output.arguments)
```

```console
$ python main.py login -u ana -p 123
login {'username': 'ana', 'password': '123'}

$ python main.py logout --all
logout {'all': True}

$ python main.py -h
usage: My App [-h] {login,logout} ...
```

The chosen command is available in `output.command`, and `output.arguments` has only the arguments of that command.
If no command is given, `output.command` is `None`.

### Running a function per command

Pass `script_entrypoint` to `add_command_parser` to call a function when its command is chosen. `get_arguments` calls it
with the parsed arguments as keyword arguments, so the function parameters must match the parser argument names. The
value returned by the function is available in `output.entrypoint_output`.

```python
class Greet(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--name", "-n", required=True)


def greet(name: str) -> str:
    print(f"Hello, {name}!")
    return name.upper()


app = App(name="My App")
app.add_command_parser(Greet(name="Greet"), script_entrypoint=greet)

output = app.get_arguments()
print(output.entrypoint_output)
```

```console
$ python main.py greet -n ana
Hello, ana!
ANA
```

## Reusing arguments

Arguments from other parsers can be inherited with `parents`:

```python
class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")


class Build(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--target")


build = Build(name="Build", pyarg_groups=Common(name="Common", add_help=False))
```

Use `add_help=False` on the parent parser so the `-h` option is not registered twice.

## API

### `PyArg(name, description=None, pyarg_groups=None, **kwargs)`

Abstract class. It cannot be instantiated directly, you must inherit from it and implement `setup_arguments`.

- `name`: parser name. Used as `prog` in the help text and to build the command name.
- `description`: text shown in `-h`.
- `pyarg_groups`: other parsers whose arguments are grouped in this one.
- `**kwargs`: forwarded to `argparse.ArgumentParser`. The `prog`, `description` and `conflict_handler`
  keys are ignored, as `conflict_handler` is always `"resolve"`.

### `setup_arguments(self) -> None`

Abstract method. Define all the arguments of the parser here. It runs at the end of `__init__`.

### `command_name`

Read-only property with the command name derived from `name`.

### `add_command_parser(parser, description=None, script_entrypoint=None)`

Adds `parser` as a sub-command. If `description` is not set, the parser's own description is used.

`script_entrypoint` is a callable to run when the command is chosen. It receives the parsed arguments as keyword
arguments. See [Running a function per command](#running-a-function-per-command).

### `get_arguments() -> PyArgOutput`

Parses `sys.argv` and returns a [`PyArgOutput`](#pyargoutput) with the arguments passed by the user.

If the chosen command has a `script_entrypoint`, it is called with those arguments before returning. Calling
`get_arguments` more than once runs it more than once, and if the function exits or raises, nothing is returned.

### `PyArgOutput`

Dataclass returned by `get_arguments`. It can be imported with `from pyarg import PyArgOutput`.

|Field|Type|Description|
|-|-|-|
|`arguments`|`dict[str, Any]`|Arguments passed by the user, without the command name.|
|`command`|`str \| None`|Name of the chosen command, or `None` if no command was given.|
|`entrypoint_output`|`Any \| None`|Value returned by the command `script_entrypoint`. It is `None` if the command has no entrypoint, or if the function returns nothing.|

## Development

See [DEVELOPERS.md](DEVELOPERS.md).
