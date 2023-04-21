"""Main class of the backup task of S3."""
from pathlib import Path
from typing import Any

from services.mc_commands import McCommands
from services.reporting import Report
from ..common import CommonS3, OnPathDirMissing


class S3(CommonS3):
    """Subtask for backup S3.

    Mirror the cluster buckets into the local Minio instance.
    """

    def __init__(self, report: Report, path_work_dir: Path, mc_commands: McCommands, buckets: list[str]):
        super().__init__(path_work_dir, mc_commands, buckets)
        self._report = report.get_sub_report("BackupS3", default_status_level="NOTIFY",
                                             init_status="ComponentInitialized")

    def prepare(self) -> None:
        """Prepare S3 backup.

        Run disk usage for cluster buckets to fill cache on instance.
        """
        self._report.debug(f"disk usage cluster buckets: {self._buckets}")
        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(f"disk_usage_{bucket}", default_status_level="NOTIFY")
            self._mc_commands.set_reporter(bucket_report)
            nb_objects, size = self._mc_commands.du_cluster_bucket(bucket)
            bucket_report.notify(f"nb_objects: {nb_objects}, size: {size}")
            bucket_report.set_status("Done")

    def run(self) -> None:
        """Run the task."""
        mc_commands = self._mc_commands

        self._report.debug(f"mirroring buckets: {self._buckets}")
        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(f"backup_minio_{bucket}", default_status_level="NOTIFY")
            mc_commands.set_reporter(bucket_report)
            mc_commands.backup_bucket(bucket)
            bucket_report.set_status("Done")

        mc_commands.set_reporter(self._report)
        mc_commands.stop_local()

    def task_path_dir_and_archive_item(self) -> tuple[Path, str]:
        """Simple getter.

        Returns:
            tuple[Path, str]: the dir path of Minio and the constant 'minio'
        """
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.ERROR)

    def metadata(self) -> Any:
        """Simple getter.

        Returns:
            dict: metadata from mc_commands
        """
        return {
            "url": self._mc_commands.cluster_url(),
            "info": self._mc_commands.cluster_info(),
        }
