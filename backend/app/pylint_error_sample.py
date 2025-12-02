"""Temporary file to test Pylint error detection."""


def test_function():
    """Function with intentional error."""
    return undefined_variable  # E0602: Undefined variable
