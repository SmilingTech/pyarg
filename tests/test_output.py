"""Tests for the PyArgOutput dataclass."""

from __future__ import annotations

import dataclasses

import pyarg
from pyarg import PyArgOutput


def test_defaults() -> None:
    output = PyArgOutput(arguments={"a": 1})
    assert output.arguments == {"a": 1}
    assert output.command is None
    assert output.entrypoint_output is None


def test_is_dataclass() -> None:
    assert dataclasses.is_dataclass(PyArgOutput)


def test_equality() -> None:
    assert PyArgOutput(arguments={"a": 1}, command="x") == PyArgOutput(arguments={"a": 1}, command="x")
    assert PyArgOutput(arguments={"a": 1}) != PyArgOutput(arguments={"a": 2})


def test_public_api() -> None:
    assert set(pyarg.__all__) >= {"PyArg", "PyArgOutput"}
