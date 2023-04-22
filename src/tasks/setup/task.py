"""Main class for setup task."""

# standard library
import os

from pathlib import Path

# typing
from typing import Optional

# data-manager assets
from assets import KnownAssets, copy_asset_to_file

# data-manager services
from services.archiver import Archiver
from services.google_drive import GoogleDrive
from services.reporting import Report


class KeycloakDetails:
    """Represent details (path to status file, script) for keycloak setup."""

    def __init__(self, path_keycloak_status_file: Path, path_keycloak_script: Path):
        """Simple constructor.

        Args:
            path_keycloak_status_file (str): the path to the keycloak status file in keycloak container directory
            path_keycloak_script (str): the path to keycloak script to execute in keycloak container
        """
        self._path_keycloak_status_file = path_keycloak_status_file
        self._path_keycloak_script = path_keycloak_script

    def path_keycloak_status_file(self) -> Path:
        """Simple getter.

        Returns:
            Path: the path of the keycloak status file
        """
        return self._path_keycloak_status_file

    def path_keycloak_script(self) -> Path:
        """Sinple getter.

        Returns:
            Path: the path of the keycloak script
        """
        return self._path_keycloak_script


class Task:
    """Task setup.

    Will download an archive and extract the specified item(s).

    Notes:
      Can be call with or without an archive name: in the latter case the last archive will be downloaded.
    """

    def __init__(
        self,
        report: Report,
        path_work_dir: Path,
        google_drive: GoogleDrive,
        archiver: Archiver,
        extract_items: list[str],
        keycloak_setup_details: Optional[KeycloakDetails] = None,
        archive_name: Optional[str] = None,
    ):
        """Simple constructor.

        Args:
            report (Report): the report
            path_work_dir (Path): the working directory path
            google_drive (GoogleDrive): the google_drive service
            archiver (Archiver): the archiver service
            extract_items (list[str]): the list of items to extract from the archive
            keycloak_setup_details (Optional[KeycloakDetails]): if provided, setup keycloak container directory
            archive_name (Optional[str]): if provided, use this google drive archive instead of the latest
        """
        self._path_work_dir = path_work_dir
        self._keycloak_setup_details = keycloak_setup_details
        self._google_drive = google_drive
        self._archiver = archiver
        self._extract_items = extract_items
        self._archive_name = archive_name
        self._report = report.get_sub_report(
            "Setup", default_status_level="NOTIFY", init_status="ComponentInitialized"
        )

    def run(self) -> None:
        """Run setup task.

        Download archive & extract item(s).
        Create keycloak directory & file status if keycloak_setup_details has been passed.
        """
        report = self._report.get_sub_report(task="run", init_status="in function")
        if self._keycloak_setup_details is not None:
            report_kc = report.get_sub_report("setup keycloak", init_status="in block")
            report_kc.debug(
                f"Set up status file '{self._keycloak_setup_details.path_keycloak_status_file()}'"
            )
            self._keycloak_setup_details.path_keycloak_status_file().parent.mkdir(
                exist_ok=True, parents=True
            )
            self._keycloak_setup_details.path_keycloak_status_file().write_text(
                "SETUP\n"
            )
            report_kc.debug(
                f"Copying kc script to '{self._keycloak_setup_details.path_keycloak_script()}'"
            )
            copy_asset_to_file(
                KnownAssets.KC_EXPORT_SH,
                self._keycloak_setup_details.path_keycloak_script(),
            )
            report_kc.debug("Done")

        if self._archive_name is None:
            self._setup_last_archive()
        else:
            self._setup_explicit_archive(self._archive_name)

    def _setup_last_archive(self) -> None:
        archives = self._google_drive.list_archives()

        if len(archives) == 0:
            self._report.warning("No archive found. Skipping setup")
            return

        last_archive = sorted(archives, key=lambda arc: arc.name())[len(archives) - 1]
        self._report.notify(
            f"using last archive : {last_archive.name()} ({last_archive.file_id()})"
        )
        self.__setup_archive(last_archive.file_id())

    def _setup_explicit_archive(self, archive_name: str) -> None:
        archive_id = self._google_drive.get_archive_id(archive_name)
        if archive_id is None:
            raise RuntimeError(
                f"Archive named {archive_name} not found in Google Drive"
            )
        self._report.notify(f"using archive : {archive_name}, ({archive_id}")
        self.__setup_archive(archive_id)

    def __setup_archive(self, archive_id: str) -> None:
        path_archive = self._path_work_dir / "setup_archive.tgz"
        self._google_drive.download(archive_id, path_file=path_archive)
        archive = self._archiver.existing_archive(path_archive=path_archive)
        for item in self._extract_items:
            archive.extract_dir_item(item)
        os.unlink(path_archive)
