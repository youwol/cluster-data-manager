"""Abstract parent class & ancillary classes for all tasks."""
from enum import Enum
from pathlib import Path


class OnPathDirMissing(Enum):
    """Enum for the behavior of Task#_path_dir_maybe_exists()."""
    CREATE = "create"
    ERROR = "error"


class Task:
    """Abstract parent class for all tasks.

    Provide a method for ensuring that a relative path exist.
    """

    def __init__(self, path_work_dir: Path):
        self._path_work_dir = path_work_dir

    def _path_dir_maybe_exists(self, relative_path: str, on_missing: OnPathDirMissing) -> Path:

        path = self._path_work_dir / relative_path
        if not path.exists():
            if on_missing == OnPathDirMissing.ERROR:
                raise RuntimeError(f"path {path} does not exist")
            if on_missing == OnPathDirMissing.CREATE:
                path.mkdir(parents=True)

        if not path.is_dir():
            raise RuntimeError(f"path '{path}' is not a directory")

        return path
