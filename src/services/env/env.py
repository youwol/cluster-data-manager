import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

load_dotenv()


def creating_file(env_name: str):
    path = not_empty_string(env_name)

    result = Path(path)

    try:
        result.touch(exist_ok=False)
    except FileExistsError:
        raise RuntimeError(f"Env {env_name} set but path '{path} already exists")
    except OSError as e:
        raise RuntimeError(f"Env {env_name} set but failed to touch path '{path} : {e.strerror}")


def existing_path(env_name: str):
    path = not_empty_string(env_name)

    result = Path(path)

    if not result.exists():
        raise RuntimeError(f"Env {env_name} set but path '{path}' does not exist")

    return result


def non_existing_path(env_name: str):
    path = not_empty_string(env_name)

    result = Path(path)

    if result.exists():
        raise RuntimeError(f"Env {env_name} set but path '{path}' exists")

    return result


def empty_dir(env_name: str):
    path = existing_path(env_name)

    if not path.is_dir():
        raise RuntimeError(f"Env {env_name} set but path is not a dir")

    if os.listdir(path):
        raise RuntimeError(f"Env {env_name} is a directory but is not empty")


def not_empty_string(env_name: str):
    result = os.getenv(env_name)

    if result is None:
        raise RuntimeError(f"Env {env_name} not set")

    if result.strip() == "":
        raise RuntimeError(f"Env {env_name} set but empty once striped")

    return result


def maybe_string(env_name: str, default: Optional[str] = None):
    result = os.getenv(env_name)

    if result is None:
        return default

    return result


def boolean(env_name: str, default: bool = None):
    true_strings = ['true', 'True', 'yes', 'y']
    false_strings = ['false', 'False', 'no', 'n']
    v = os.getenv(env_name)

    if v is None:
        if default is None:
            raise RuntimeError(f"Env {env_name} not set")
        else:
            return default

    if v in true_strings:
        return True

    if v in false_strings:
        return False

    raise RuntimeError(f"Env {env_name} expect a boolean but is set to '{v}'")


def integer(env_name: str, default: int = None):
    v = os.getenv(env_name)

    if v is None:
        if default is None:
            raise RuntimeError(f"Env {env_name} not set")
        else:
            return default

    if str(int(v)) == v:
        return int(v)
    else:
        raise RuntimeError(f"Env {env_name} expect an integer but is set to '{v}'")


def strings_list(env_name, sep: str = ":"):
    string_list = not_empty_string(env_name)

    return string_list.split(sep)
