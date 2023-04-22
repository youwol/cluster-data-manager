"""Parent class for keycloak tasks."""
from pathlib import Path

from .task import OnPathDirMissing, Task


class Keycloak(Task):
    """Parent class for keycloak tasks.

    Define relative path for tasks.
    """

    RELATIVE_PATH = "kc"

    def _task_path_dir_and_archive_item(self, on_missing: OnPathDirMissing) -> tuple[Path, str]:
        return self._path_dir_maybe_exists(
            Keycloak.RELATIVE_PATH,
            on_missing=on_missing
        ), Keycloak.RELATIVE_PATH
