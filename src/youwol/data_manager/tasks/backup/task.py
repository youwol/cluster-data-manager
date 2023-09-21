"""The backup task itself."""
# standard library
from abc import ABC, abstractmethod
from pathlib import Path

# typing
from typing import Any, List

# application configuration
from youwol.data_manager.configuration import ArchiveItem

# application services
from youwol.data_manager.services.archiver import ArchiveCreator
from youwol.data_manager.services.cluster_maintenance import ContextMaintenance
from youwol.data_manager.services.containers_readiness import ContainersReadiness
from youwol.data_manager.services.google_drive import GoogleDrive


class BackupSubtask(ABC):
    @abstractmethod
    def metadata(self) -> tuple[str, Any]:
        """Key & value to add to archive metadata."""

    @abstractmethod
    def prepare(self) -> None:
        """Work to be done before run()

        Notes:
            This methode is called outside the Maintenance context

        """

    @abstractmethod
    def run(self) -> None:
        """The task itself"""

    @abstractmethod
    def task_path_dir_and_archive_item(self) -> tuple[Path, ArchiveItem]:
        """Return the path to the data directory and the expected entry in the archive"""


class Task:
    """TaskBackup.

    Prepare archive metadata, run subtasks and upload archive to Google Drive.
    """

    def __init__(
        self,
        containers_readiness: ContainersReadiness,
        subtasks: List[BackupSubtask],
        archive: ArchiveCreator,
        google_drive: GoogleDrive,
        google_drive_upload_file_name: str,
        google_drive_upload_folder: str,
        context_maintenance: ContextMaintenance,
        path_log_file: Path,
    ):
        """Simple constructor.

        Args:
            containers_readiness: the containers readiness service
            subtasks (BackupSubtask): list of subtasks to run
            archive (ArchiveCreator): the archive creator
            google_drive (GoogleDrive): the google drive service
            google_drive_upload_file_name (str): the name of the google drive upload
            google_drive_upload_folder (str): the folder name for the google drive upload
            cluster_maintenance (ClusterMaintenance): the cluster maintenance service
            path_log_file (Path): the path to the log file
        """
        self._containers_readiness = containers_readiness
        self._subtasks = subtasks
        self._archive = archive
        self._google_drive = google_drive
        self._upload_file_name = google_drive_upload_file_name
        self._upload_folder = google_drive_upload_folder
        self._context_maintenance = context_maintenance
        self._path_log_file = path_log_file

    def run(self) -> None:
        """Run the task."""
        self._containers_readiness.wait()

        for subtask in self._subtasks:
            self._archive.add_metadata(*subtask.metadata())
        self._archive.add_metadata(
            "GoogleDrive",
            {
                "account": self._google_drive.account(),
                "driveID": self._google_drive.drive_id(),
            },
        )

        for subtask in self._subtasks:
            subtask.prepare()

        with self._context_maintenance:
            for subtask in self._subtasks:
                subtask.run()

        for subtask in self._subtasks:
            self._archive.add_dir_item(*subtask.task_path_dir_and_archive_item())
        self._archive.add_file_item(self._path_log_file, "backup.log")

        path_archive = self._archive.finalize()
        self._google_drive.upload(
            path_local_file=path_archive,
            file_name=self._upload_file_name,
            folder_name=self._upload_folder,
        )
