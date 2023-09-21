"""Parent class for keycloak tasks."""
# standard library
import time

from pathlib import Path

# typing
from typing import Callable, Optional

# application configuration
from youwol.data_manager.configuration import (
    ArchiveItem,
    Deployment,
    KeycloakStatus,
    env_utils,
)

# application services
from youwol.data_manager.services import get_service_report_builder
from youwol.data_manager.services.keycloak_admin import (
    KeycloakAdmin,
    KeycloakAdminCredentials,
)
from youwol.data_manager.services.reporting import Report

# relative
from .subtask import OnPathDirMissing, Subtask


class Context:
    keycloak_admin: Optional[KeycloakAdmin] = None


context = Context()


def get_keycloak_admin_builder() -> Callable[[], KeycloakAdmin]:
    """Get a builder for a configured instance of the keycloak admin service.

    Returns:
        Callable[[], KeycloakAdmin]: a nullary builder for an instance of keycloak admin service
    """
    if context.keycloak_admin is not None:
        keycloak_admin = context.keycloak_admin
        return lambda: keycloak_admin

    report_builder = get_service_report_builder()

    def builder() -> KeycloakAdmin:
        if context.keycloak_admin is None:
            keycloak_username = env_utils.not_empty_string(Deployment.KEYCLOAK_USERNAME)
            keycloak_password = env_utils.not_empty_string(Deployment.KEYCLOAK_PASSWORD)
            keycloak_base_url = env_utils.not_empty_string(Deployment.KEYCLOAK_BASE_URL)
            context.keycloak_admin = KeycloakAdmin(
                report=report_builder(),
                credentials=KeycloakAdminCredentials(
                    realm="master",
                    username=keycloak_username,
                    password=keycloak_password,
                ),
                base_url=keycloak_base_url,
            )

        return context.keycloak_admin

    return builder


class Keycloak(Subtask):
    """Parent class for keycloak tasks.

    Define relative path for tasks.
    """

    def __init__(
        self,
        path_work_dir: Path,
        report: Report,
        keycloak_admin: KeycloakAdmin,
        path_keycloak_status_file: Path,
    ):
        super().__init__(path_work_dir)
        self._report = report.get_sub_report(
            "Keycloak",
            default_status_level="NOTIFY",
            init_status="ComponentInitialized",
        )
        self._keycloak_admin = keycloak_admin
        self._path_status_file = path_keycloak_status_file

    def _task_path_dir_and_archive_item(
        self, on_missing: OnPathDirMissing
    ) -> tuple[Path, ArchiveItem]:
        return (
            self._path_dir_maybe_exists(
                ArchiveItem.KEYCLOAK.value, on_missing=on_missing
            ),
            ArchiveItem.KEYCLOAK,
        )

    def run(self) -> None:
        """Run the task.

        Commands are run from an other script in keycloak container. This method watch a status file updated by this
        script and wait for the status of the script to be "DONE".
        """
        report = self._report.get_sub_report(task="run", init_status="in function")
        status = self._path_status_file.read_text("UTF-8").strip()
        previous_status = None
        while status != KeycloakStatus.DONE.value:
            if status == KeycloakStatus.ERROR.value:
                report.fatal(f"Status file is {status}")
                raise RuntimeError(
                    f"Status file is {status} : see keycloak container logs"
                )
            if status != previous_status:
                previous_status = status
                report.notify(f"New status '{status}'")
            else:
                report.debug(f"Status is still '{status}'")
            time.sleep(5)
            status = self._path_status_file.read_text("UTF-8").strip()
        report.notify("Done")
