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

`name` is optional. When it is not given, the class name is used, so `Login()` is the same as `Login(name="Login")`.

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
app.add_command_parser(Logout(name="Logout", description="Sign out."))

output = app.get_arguments()
print(output.command, output.arguments)
```

```console
$ python main.py login -u ana -p 123
login {'username': 'ana', 'password': '123'}

$ python main.py logout --all
logout {'all': True}

$ python main.py -h
usage: My App [-h] [--tree] {login,logout} ...
```

Commands can also be passed when creating the parser, with `pyarg_commands`:

```python
app = App(name="My App", pyarg_commands=[Login(description="Sign in."), Logout(description="Sign out.")])
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

The function can also be set on the parser itself with the `entrypoint` property. It is used when the command is
added without a `script_entrypoint`, which also works with `pyarg_commands`:

```python
greet_parser = Greet(name="Greet")
greet_parser.entrypoint = greet

app = App(name="My App", pyarg_commands=greet_parser)
```

The `entrypoint` of the main parser runs when no command is chosen.

## Reusing arguments

Arguments from other parsers can be inherited with `pyarg_groups`. They'll be grouped by it own PyArg `name`:

```python
class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")


class Build(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--target")


build = Build(name="Build", pyarg_groups=Common(name="Common"))
```

## Tree view

`tree()` prints the whole structure of a parser: its own arguments, the `pyarg_groups` and the commands, recursively.
Each argument shows its type, default value, `help` text and whether it is required. Groups show their `name` and
commands show the name used to call them (`[$ greet]`), both followed by the `description` when it is set.

The type is inferred from the argument: `type`, the action (`store_true` is `bool`, `count` is `int`), `choices`,
`default` and `nargs` (`append` or `nargs="+"` give `list[...]`). When nothing tells the type, it is `str`.

```python
class Greet(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--name", "-n", required=True, help="Person to greet.")


class Common(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--verbose", "-v", action="store_true")
        self.add_argument("--target", default="local")


class App(PyArg):
    def setup_arguments(self) -> None:
        self.add_argument("--run", "-r", action="store_true", help="Run it.")


app = App(name="Application", pyarg_groups=Common(name="Common Arguments"))
app.add_command_parser(Greet())
app.tree()
```

```console
App(name=Application, description=None)
├── --run, -r ; type=bool: Run it.
├── [group] Common Arguments
│   ├── --verbose, -v ; type=bool
│   └── --target ; type=str ; default=local
└── [command] Greet [$ greet]
    └── --name, -n ; type=str: Person to greet. (required)
```

In the terminal, `group` and `command` are colored.

Every parser also has a `--tree` option that prints the tree and exits, like `-h`. On a command, it prints only the
tree of that command:

```console
$ python main.py --tree
$ python main.py greet --tree
```

The `--tree` option is not shown in the tree and is not returned in `output.arguments`.

## API

### `PyArg(name=None, description=None, pyarg_groups=None, pyarg_commands=None, **kwargs)`

Abstract class. It cannot be instantiated directly, you must inherit from it and implement `setup_arguments`.

- `name`: parser name. Used as `prog` in the help text and to build the command name. Defaults to the class name.
- `description`: text shown in `-h`.
- `pyarg_groups`: other parsers whose arguments are grouped in this one.
- `pyarg_commands`: other parsers added as sub-commands, the same as calling `add_command_parser` for each one.
- `**kwargs`: forwarded to `argparse.ArgumentParser`. The `prog`, `description` and `conflict_handler`
  keys are ignored, as `conflict_handler` is always `"resolve"`.

### `setup_arguments(self) -> None`

Abstract method. Define all the arguments of the parser here. It runs at the end of `__init__`.

### `command_name`

Read-only property with the command name derived from `name`.

### `name`

Read-only property with the parser name.

### `entrypoint`

Function called by `get_arguments` with the parsed arguments. When the parser is added as a command without a
`script_entrypoint`, this one is used. By default it does nothing and returns `None`.

### `add_command_parser(parser, script_entrypoint=None)`

Adds `parser` as a sub-command.

`script_entrypoint` is a callable to run when the command is chosen. It receives the parsed arguments as keyword
arguments. If it is not set, the parser's own [`entrypoint`](#entrypoint) is used. See
[Running a function per command](#running-a-function-per-command).

### `tree() -> None`

Prints the parser structure as a tree. The same as passing `--tree` in the CLI. See [Tree view](#tree-view).

### `get_arguments() -> PyArgOutput`

Parses `sys.argv` and returns a [`PyArgOutput`](#pyargoutput) with the arguments passed by the user.

The entrypoint of the chosen command (or of the main parser, if no command was given) is called with those arguments
before returning. Calling `get_arguments` more than once runs it more than once, and if the function exits or raises,
nothing is returned.

### `PyArgOutput`

Dataclass returned by `get_arguments`. It can be imported with `from pyarg import PyArgOutput`.

|Field|Type|Description|
|-|-|-|
|`arguments`|`dict[str, Any]`|Arguments passed by the user, without the command name.|
|`command`|`str \| None`|Name of the chosen command, or `None` if no command was given.|
|`entrypoint_output`|`Any \| None`|Value returned by the entrypoint. It is `None` if no entrypoint was set, or if the function returns nothing.|

## Development

See [DEVELOPERS.md](DEVELOPERS.md).
