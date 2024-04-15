"""Utilitary fonctions for environement variables."""

# standard library
import os
import sys

from pathlib import Path

# typing
from typing import Optional

# third parties
from dotenv import load_dotenv

# relative
from .env_vars import EnvironmentVars

TRUE_STRINGS = ["true", "True", "yes", "y"]
FALSE_STRINGS = ["false", "False", "no", "n"]

load_dotenv()


class FileCreationError(RuntimeError):
    """Simple RuntimeError for file creation failure."""

    def __init__(self, msg: str):
        """Simply Call super.

        Args:
            msg (str): message passed to parent class.
        """
        super().__init__(msg)


class EnvVarNotSet(RuntimeError):
    """Simple RuntimeError for environment variable not set."""

    def __init__(self, env_name: EnvironmentVars):
        """Call super with a formatted message.

        Args:
            env_name (EnvironmentVars): the environment variable not set.
        """
        super().__init__(f"Env {env_name.value} not set")


class EnvVarEmpty(RuntimeError):
    """Simple RuntimeError for empty (once stripped) environment variable."""

    def __init__(self, env_name: EnvironmentVars):
        """Call super with a formatted message.

        Args:
            env_name (EnvironmentVars): the empty environment variable.
        """
        super().__init__(f"Env {env_name.value} set but empty once striped")


class DirNotEmptyError(RuntimeError):
    """Simple RuntimeError for an expected empty dir containing entries."""

    def __init__(self, env_name: EnvironmentVars, dir_path: Path):
        """Call super with a formatted message.

        Args:
            env_name (EnvironmentVars): the environment variable.
            dir_path (Path): the path of the (not empty) directory.
        """
        super().__init__(
            f"Directory {dir_path} defined in env {env_name.value} is not empty"
        )


class BooleanParsingError(RuntimeError):
    """Simple RuntimeError for an environment variable expected to be a boolean but not parsable."""

    def __init__(self, env_name: EnvironmentVars, value: str):
        """Call super with a formatted message.

        Args:
            env_name (EnvironmentVars): the environment variable.
            value (str): the (unparseable) value.
        """
        super().__init__(
            f"Env {env_name.value} value '{value}' could not be parse as a boolean"
        )


class IntegerParsingError(RuntimeError):
    """Simple RuntimeError for an environment variable expected to be an integer but not parsable."""

    def __init__(self, env_name: EnvironmentVars, value: str):
        """Call super with a formatted message.

        Args:
            env_name (EnvironmentVars): the environment variable.
            value (str): the (unparseable) value.
        """
        super().__init__(
            f"Env {env_name.value} value '{value}' could not be parse as an integer"
        )


def file(env_name: EnvironmentVars) -> Path:
    """Get a Path from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.

    Returns:
        Path: a path.

    Raises:
       EnvVarNotSet: if the environment variable is not set.
       EnvVarEmpty: if the environment variable is an empty string once stripped.
    """
    return Path(not_empty_string(env_name))


def creating_file(env_name: EnvironmentVars) -> Path:
    """Get a Path to a new file from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.

    Returns:
        Path: a path to a newly created file.

    Raises:
       EnvVarNotSet: if the environment variable is not set.
       EnvVarEmpty: if the environment variable is an empty string once stripped.
       FileCreationError: if the file already exists or cannot be created.
    """
    result = Path(not_empty_string(env_name))

    try:
        result.parent.mkdir(parents=True, exist_ok=True)
        result.touch(exist_ok=False)
    except FileExistsError as error:
        raise FileCreationError(
            f"Path '{result}' defined in {env_name.value} already exists"
        ) from error
    except OSError as error:
        raise FileCreationError(
            f"Failed to touch path '{result}' defined in {env_name.value}"
        ) from error

    return result


def existing_path(env_name: EnvironmentVars) -> Path:
    """Get a Path to an existing file from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.

    Returns:
        Path: a path to a existing file.

    Raises:
       EnvVarNotSet: if the environment variable is not set.
       EnvVarEmpty: if the environment variable is an empty string once stripped.
       FileNotFoundError: if the file does not exist.
    """
    result = Path(not_empty_string(env_name))

    if not result.exists():
        raise FileNotFoundError(
            f"Path '{result}' defined in env {env_name.value} does not exist"
        )

    return result


def non_existing_path(env_name: EnvironmentVars) -> Path:
    """Get a Path to a non-existing file from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.

    Returns:
        Path: a path to a non-existing file.

    Raises:
      EnvVarNotSet: if the environment variable is not set.
      EnvVarEmpty: if the environment variable is an empty string once stripped.
      FileExistsError: if the file exists.
    """
    result = Path(not_empty_string(env_name))

    if result.exists():
        raise FileExistsError(f"Path '{result}' defined in env {env_name.value} exists")

    return result


def empty_dir(env_name: EnvironmentVars, create: bool = True) -> Path:
    """Get a Path to an empty dir from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.
        create (bool): if directory does not exist, it will be created

    Returns:
        Path: the directory path.
    """
    result = Path(not_empty_string(env_name))

    if create and not result.exists():
        result.mkdir(parents=True)

    if not result.exists():
        raise FileNotFoundError(
            f"Path '{result}' defined in env {env_name.value} does not exist"
        )

    if not result.is_dir():
        raise NotADirectoryError(
            f"Path '{result}' defined in env {env_name.value} is not a dir"
        )

    if os.listdir(result):
        raise DirNotEmptyError(env_name, result)

    return result


def not_empty_string(env_name: EnvironmentVars) -> str:
    """Get a non empty string from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.

    Returns:
        str: a non empty string

    Raises:
       EnvVarNotSet: if the environment variable is not set.
       EnvVarEmpty: if the environment variable is an empty string once stripped.
    """
    result = os.getenv(env_name.value)

    if result is None:
        raise EnvVarNotSet(env_name)

    if result.strip() == "":
        raise EnvVarEmpty(env_name)

    return result


def maybe_string(
    env_name: EnvironmentVars, default: Optional[str] = None
) -> Optional[str]:
    """Get a string from an environment variable or the default if not set.

    If not provided default is None.

    Args:
        env_name (EnvVars): environment variable name.
        default (Optional[str]): default value if environment variable is not set.

    Returns:
        Optional[str]: either the value from the environment variable or the default value.

    """
    result = os.getenv(env_name.value)

    if result is None:
        return default

    return result


def boolean(env_name: EnvironmentVars, default: Optional[bool] = None) -> bool:
    """Get a boolean from an environment variable.

    True is either 'True', 'true', 'yes' or 'y', after stripping.
    False is either 'False', 'false', 'no' or 'n', after stripping.

    If the default is not provided or is None, then the variable must be set.
    If the default is provided and is a boolean, that value will be returned if the environment variable is not set.

    Args:
        env_name (EnvVars): environnent variable name.
        default (Optional[bool]): default value if environment is not set.

    Returns:
        bool: the boolean.

    Raises:
        EnvVarNotSet: if the environment variable is not set and default is not provided or is None.
        BooleanParsingError: if the value is not parsable as a boolean.
    """
    str_value = os.getenv(env_name.value)

    if str_value is None:
        if default is None:
            raise EnvVarNotSet(env_name)
        return default

    if str_value.strip() in TRUE_STRINGS:
        return True

    if str_value.strip() in FALSE_STRINGS:
        return False

    raise BooleanParsingError(env_name, str_value)


def integer(env_name: EnvironmentVars, default: Optional[int] = None) -> int:
    """Get an integer from an environment variable.

    Use str(int(<value>)) == v.strip() to check integer parsing.

    If the default is not provided or is None, then the variable must be set.
    If the default is provided and is a boolean, that value will be returned if the environment variable is not set.

    Args:
        env_name (EnvVars): environment variable name.
        default (Optional[int]): default value if environment is not set.

    Returns:
        int: the integer.

    Raises:
        EnvVarNotSet: if the environment variable is not set and default is not provided or is None.
        IntegerParsingError: if the value is not parsable as ar integer.
    """
    str_value = os.getenv(env_name.value)

    if str_value is None:
        if default is None:
            raise EnvVarNotSet(env_name)
        return default

    if str(int(str_value)) != str_value.strip():
        raise IntegerParsingError(env_name, str_value)

    return int(str_value)


def strings_list(env_name: EnvironmentVars, sep: str = ":") -> list[str]:
    """Split env_name in a list of str.

    Notes:
        The environment variable must be set.
        To pass an empty list, just set it to the separator alone : ENV=":"
        To make that environment variable entirely optional, use maybe_strings_list()

    Args:
        env_name (EnvironmentVars): environment variable name
        sep (str): the separator (':' by default)

    Returns:
        list[str]: a list of string, possibly empty
    """
    string_list = not_empty_string(env_name)

    return [item.strip() for item in string_list.split(sep) if item.strip() != ""]


def maybe_strings_list(
    env_name: EnvironmentVars, default: Optional[list[str]] = None, sep: str = ":"
) -> list[str]:
    """Split env_name in a list of str or return default if not set.

    If not provided default is an empty list.

    Notes:
        To pass an empty list, just set it to the separator alone : ENV=":"

    Args:
        env_name (EnvironmentVars): environment variable name
        default (Optional[list[str]): default value if environment is not set.
        sep (str): the separator (':' by default)

    Returns:
        list[str]: a list of string, possibly empty
    """

    string_list = maybe_string(env_name)

    if string_list is None:
        return [] if default is None else default

    return strings_list(env_name, sep)


def arg_task_name() -> str:
    """Get the task name from command line.

    The task name is expected as the sole argument on command line.

    Returns:
        str: the task name
    """
    if len(sys.argv) != 2:
        raise RuntimeError(f"{sys.argv[0]} expect exactly one argument")

    return sys.argv[1]
