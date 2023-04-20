"""Parent class for keycloak tasks"""
from pathlib import Path

from tasks.common import OnPathDirMissing
from tasks.common.task import Task


class TaskKeycloak(Task):
    """Parent class for keycloak tasks.

    Define relative path for tasks.
    """
    RELATIVE_PATH = "kc"

    def _task_path_dir_and_archive_item(self, on_missing: OnPathDirMissing) -> tuple[Path, str]:
        return self._path_dir_maybe_exists(
            TaskKeycloak.RELATIVE_PATH,
            on_missing=on_missing
        ), TaskKeycloak.RELATIVE_PATH
