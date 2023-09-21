"""Parent class for keycloak tasks."""
# standard library
from pathlib import Path

# relative
from ...configuration import ArchiveItem
from .subtask import OnPathDirMissing, Subtask


class Keycloak(Subtask):
    """Parent class for keycloak tasks.

    Define relative path for tasks.
    """

    def _task_path_dir_and_archive_item(
        self, on_missing: OnPathDirMissing
    ) -> tuple[Path, ArchiveItem]:
        return (
            self._path_dir_maybe_exists(
                ArchiveItem.KEYCLOAK.value, on_missing=on_missing
            ),
            ArchiveItem.KEYCLOAK,
        )
