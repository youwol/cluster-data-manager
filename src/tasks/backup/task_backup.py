from pathlib import Path

from services.archiver import NewArchive
from services.cluster_maintenance import ClusterMaintenance
from services.google_drive import GoogleDrive
from tasks.backup.task_backup_cassandra import TaskBackupCassandra
from tasks.backup.task_backup_s3 import TaskBackupS3


class TaskBackup:

    def __init__(self,
                 task_backup_s3: TaskBackupS3,
                 task_backup_cassandra: TaskBackupCassandra,
                 archive: NewArchive,
                 google_drive: GoogleDrive,
                 google_drive_upload_file_name: str,
                 google_drive_upload_folder: str,
                 cluster_maintenance: ClusterMaintenance,
                 path_log_file: Path
                 ):
        self._task_backup_s3 = task_backup_s3
        self._task_backup_cassandra = task_backup_cassandra
        self._archive = archive
        self._google_drive = google_drive
        self._upload_file_name = google_drive_upload_file_name
        self._upload_folder = google_drive_upload_folder
        self._cluster_maintenance = cluster_maintenance
        self._path_log_file = path_log_file

    def run(self):
        self._archive.add_metadata("cassandra", self._task_backup_cassandra.metadata())
        self._archive.add_metadata("s3", self._task_backup_s3.metadata())

        self._cluster_maintenance.start_maintenance_mode()
        self._task_backup_cassandra.run()
        self._task_backup_s3.run()
        self._cluster_maintenance.stop_maintenance_mode()

        self._archive.add_dir_item(*self._task_backup_cassandra.task_path_dir_and_archive_item())
        self._archive.add_dir_item(*self._task_backup_s3.task_path_dir_and_archive_item())
        self._archive.add_file_item(self._path_log_file, "backup.log")

        path_archive = self._archive.finalize()
        self._google_drive.upload(path_local_file=path_archive, file_name=self._upload_file_name,
                                  folder_name=self._upload_folder)
