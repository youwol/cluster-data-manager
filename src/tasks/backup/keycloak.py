"""Main class for subtask backup keycloak."""
import time
from pathlib import Path
from typing import Any

from services.keycloak_admin import KeycloakAdmin
from services.reporting import Report
from ..common import CommonKeycloak, OnPathDirMissing


class Keycloak(CommonKeycloak):
    """Sub task for keycloak backup."""

    def __init__(self, report: Report,
                 keycloak_admin: KeycloakAdmin,
                 path_work_dir: Path,
                 path_keycloak_status_file: Path):
        """Simple constructor.

        Will call CommonKeycloak __init__ with path_work_dir

        Args:
            report (Report): the report
            keycloak_admin (KeycloakAdmin): the keycloak admin service
            path_work_dir (Path): the working directory path
            path_keycloak_status_file (Path): the path to the keycloak status file
        """
        super().__init__(path_work_dir)
        self._report = report
        self._keycloak_admin = keycloak_admin
        self._path_status_file = path_keycloak_status_file

    def run(self) -> None:
        """Run the task.

        Commands are run from an other script in keycloak container. This method watch a status file updated by this
        script and wait for the status of the script to be "DONE".
        """
        report = self._report.get_sub_report(task="run", init_status="in function")
        status = self._path_status_file.read_text("UTF-8").strip()
        previous_status = None
        while status != "DONE":
            if status == "ERROR":
                report.fatal("Status file is ERROR")
                raise RuntimeError("Status file is ERROR : see keycloak container logs")
            if status != previous_status:
                previous_status = status
                report.notify(f"New status '{status}'")
            else:
                report.debug(f"Status is still '{status}'")
            time.sleep(5)
            status = self._path_status_file.read_text("UTF-8").strip()
        report.notify("Done")

    def task_path_dir_and_archive_item(self) -> tuple[Path, str]:
        """Simple getter.

        Returns:
            tuple[Path, str]: the dir path of keycloak and the constant 'kc'
        """
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.CREATE)

    def metadata(self) -> Any:
        """Metadata from keycloak instance.

        Returns:
            Any: result of /admin/serverinfo
        """
        return {
            "server_info": self._keycloak_admin.system_info()
        }
