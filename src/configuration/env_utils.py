"""Utilitary fonctions for environement variables."""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

from configuration.env_vars import EnvVars

TRUE_STRINGS = ['true', 'True', 'yes', 'y']
FALSE_STRINGS = ['false', 'False', 'no', 'n']

load_dotenv()


class FileCreationError(RuntimeError):
    """Simple RuntimeError for file creation failure"""

    def __init__(self, msg):
        super().__init__(msg)


class EnvVarNotSet(RuntimeError):
    """Simple RuntimeError for environment variable not set."""

    def __init__(self, env_name: EnvVars):
        super().__init__(f"Env {env_name.value} not set")


class EnvVarEmpty(RuntimeError):
    """Simple RuntimeError for environment variable is an empty string once stripped."""

    def __init__(self, env_name: EnvVars):
        super().__init__(f"Env {env_name.value} set but empty once striped")


class DirNotEmptyError(RuntimeError):
    """Simple RuntimeError for an expected empty dir containing entries."""

    def __init__(self, env_name: EnvVars, dir_path: Path):
        super().__init__(f"Directory {dir_path} defined in env {env_name.value} is not empty")


class BooleanParsingError(RuntimeError):
    """Simple RuntimeError for an environment variable expected to be a boolean but not parsable"""

    def __init__(self, env_name: EnvVars, value: str):
        super().__init__(f"Env {env_name.value} value '{value}' could not be parse as a boolean")


class IntegerParsingError(RuntimeError):
    """Simple RuntimeError for an environment variable expected to be an integer but not parsable"""

    def __init__(self, env_name: EnvVars, value: str):
        super().__init__(f"Env {env_name.value} value '{value}' could not be parse as an integer")


def file(env_name: EnvVars) -> Path:
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


def creating_file(env_name: EnvVars) -> Path:
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
        result.touch(exist_ok=False)
    except FileExistsError as error:
        raise FileCreationError(f"Path '{result}' defined in {env_name.value} already exists") from error
    except OSError as error:
        raise FileCreationError(f"Failed to touch path '{result}' defined in {env_name.value}") from error

    return result


def existing_path(env_name: EnvVars) -> Path:
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
        raise FileNotFoundError(f"Path '{result}' defined in env {env_name.value} does not exist")

    return result


def non_existing_path(env_name: EnvVars) -> Path:
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


def empty_dir(env_name: EnvVars) -> Path:
    """Get a Path to an empty dir from an environment variable.

    Args:
        env_name (EnvVars): environment variable name.

    Returns:

    """
    result = existing_path(env_name)

    if not result.is_dir():
        raise NotADirectoryError(f"Path '{result}' defined in env {env_name.value} is not a dir")

    if os.listdir(result):
        raise DirNotEmptyError(env_name, result)

    return result


def not_empty_string(env_name: EnvVars) -> str:
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


def maybe_string(env_name: EnvVars, default: Optional[str] = None) -> Optional[str]:
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


def boolean(env_name: EnvVars, default: Optional[bool] = None) -> bool:
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


def integer(env_name: EnvVars, default: Optional[int] = None) -> int:
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


def strings_list(env_name: EnvVars, sep: str = ":") -> list[str]:
    """
    TODO: write doc
    Args:
        env_name ():
        sep ():

    Returns:

    """
    string_list = not_empty_string(env_name)

    return string_list.split(sep)


def arg_task_name():
    """
    TODO: write doc
    Returns:

    """
    if len(sys.argv) != 2:
        raise RuntimeError(f"{sys.argv[0]} expect exactly one argument")

    return sys.argv[1]
