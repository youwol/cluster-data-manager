"""The backup task itself."""
from pathlib import Path

from services.archiver import ArchiveCreator
from services.cluster_maintenance import ClusterMaintenance
from services.google_drive import GoogleDrive
from .cassandra import Cassandra
from .keycloak import Keycloak
from .s3 import S3


class Task:
    """TaskBackup.

    Prepare archive metadata, run subtasks and upload archive to Google Drive.
    """

    def __init__(self,
                 task_backup_s3: S3,
                 task_backup_cassandra: Cassandra,
                 task_backup_keycloak: Keycloak,
                 archive: ArchiveCreator,
                 google_drive: GoogleDrive,
                 google_drive_upload_file_name: str,
                 google_drive_upload_folder: str,
                 cluster_maintenance: ClusterMaintenance,
                 path_log_file: Path
                 ):
        """Simple constructor.

        Args:
            task_backup_s3 (S3): the backup S3 task
            task_backup_cassandra (Cassandra): the backup cassandra task
            task_backup_keycloak (Keycloak): the backup keycloak task
            archive (ArchiveCreator): the archive creator
            google_drive (GoogleDrive): the google drive service
            google_drive_upload_file_name (str): the name of the google drive upload
            google_drive_upload_folder (str): the folder name for the google drive upload
            cluster_maintenance (ClusterMaintenance): the cluster maintenance service
            path_log_file (Path): the path to the log file
        """
        self._task_backup_s3 = task_backup_s3
        self._task_backup_cassandra = task_backup_cassandra
        self._task_backup_keycloak = task_backup_keycloak
        self._archive = archive
        self._google_drive = google_drive
        self._upload_file_name = google_drive_upload_file_name
        self._upload_folder = google_drive_upload_folder
        self._cluster_maintenance = cluster_maintenance
        self._path_log_file = path_log_file

    def run(self) -> None:
        """Run the task."""
        self._archive.add_metadata("cql", self._task_backup_cassandra.metadata())
        self._archive.add_metadata("s3", self._task_backup_s3.metadata())
        self._archive.add_metadata("kc", self._task_backup_keycloak.metadata())
        self._archive.add_metadata(
            "GoogleDrive",
            {
                "account": self._google_drive.account(),
                "driveID": self._google_drive.drive_id()
            }
        )

        self._task_backup_s3.prepare()

        with self._cluster_maintenance:
            self._task_backup_cassandra.run()
            self._task_backup_s3.run()
            self._task_backup_keycloak.run()

        self._archive.add_dir_item(*self._task_backup_cassandra.task_path_dir_and_archive_item())
        self._archive.add_dir_item(*self._task_backup_s3.task_path_dir_and_archive_item())
        self._archive.add_dir_item(*self._task_backup_keycloak.task_path_dir_and_archive_item())
        self._archive.add_file_item(self._path_log_file, "backup.log")

        path_archive = self._archive.finalize()
        self._google_drive.upload(path_local_file=path_archive, file_name=self._upload_file_name,
                                  folder_name=self._upload_folder)
