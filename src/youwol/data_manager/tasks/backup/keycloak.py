"""Main class for subtask backup keycloak."""

# standard library
from pathlib import Path

# typing
from typing import Any

# application configuration
from youwol.data_manager.configuration import ArchiveItem

# application services
from youwol.data_manager.services.keycloak_admin import KeycloakAdmin
from youwol.data_manager.services.reporting import Report

# relative
from ..common import CommonKeycloak, OnPathDirMissing
from .task import BackupSubtask


class Keycloak(CommonKeycloak, BackupSubtask):
    """Sub task for keycloak backup."""

    def __init__(
        self,
        report: Report,
        keycloak_admin: KeycloakAdmin,
        path_work_dir: Path,
        path_keycloak_status_file: Path,
    ):
        """Simple constructor.

        Will call CommonKeycloak __init__ with path_work_dir

        Args:
            report (Report): the report
            keycloak_admin (KeycloakAdmin): the keycloak admin service
            path_work_dir (Path): the working directory path
            path_keycloak_status_file (Path): the path to the keycloak status file
        """
        super().__init__(
            path_work_dir,
            report=report,
            keycloak_admin=keycloak_admin,
            path_keycloak_status_file=path_keycloak_status_file,
        )

    def metadata(self) -> tuple[str, Any]:
        """Metadata from keycloak instance.

        Returns:
            tuple[str, Any]: key and value for keycloak (from /admin/serverinfo)
        """
        return "kc", {"server_info": self._keycloak_admin.system_info()}

    def prepare(self) -> None:
        """Nothing to da."""

    def task_path_dir_and_archive_item(self) -> tuple[Path, ArchiveItem]:
        """Simple getter.

        Returns:
            tuple[Path, str]: the dir path of keycloak and the constant 'kc'
        """
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.CREATE)
