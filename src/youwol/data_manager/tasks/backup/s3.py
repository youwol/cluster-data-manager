"""Main class of the backup task of S3."""

# standard library
from pathlib import Path

# typing
from typing import Any

# application services
from youwol.data_manager.services.mc_commands import McCommands
from youwol.data_manager.services.reporting import Report

# relative
from ...configuration import ArchiveItem
from ..common import CommonS3, OnPathDirMissing
from .task import BackupSubtask


class S3(CommonS3, BackupSubtask):
    """Subtask for backup S3.

    Mirror the cluster buckets into the local Minio instance.
    """

    def __init__(
        self,
        report: Report,
        path_work_dir: Path,
        mc_commands: McCommands,
        buckets: list[str],
    ):
        """Simple constructor.

        Will call CommanS3 __init__ with path_work_dir, mc_commands, buckets.

        Args:
            report (Report): the report
            path_work_dir (Path): the working directory path
            mc_commands (McCommands): the mc_commands service
            buckets (list[str]): the list of buckets
        """
        super().__init__(path_work_dir, mc_commands, buckets)
        self._report = report.get_sub_report(
            "BackupS3",
            default_status_level="NOTIFY",
            init_status="ComponentInitialized",
        )

    def metadata(self) -> tuple[str, Any]:
        """Simple getter.

        Returns:
            tuple[str, Any]: key and value for s3 (from mc_commands)
        """
        return "s3", {
            "url": self._mc_commands.cluster_url(),
            "info": self._mc_commands.cluster_info(),
        }

    def prepare(self) -> None:
        """Prepare S3 backup.

        Run disk usage for cluster buckets to fill cache on instance.
        """
        self._report.debug(f"disk usage cluster buckets: {self._buckets}")
        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(
                f"disk_usage_{bucket}", default_status_level="NOTIFY"
            )
            self._mc_commands.set_reporter(bucket_report)
            nb_objects, size = self._mc_commands.du_cluster_bucket(bucket)
            bucket_report.notify(f"nb_objects: {nb_objects}, size: {size}")
            bucket_report.set_status("Done")

    def run(self) -> None:
        """Run the task."""
        mc_commands = self._mc_commands

        self._report.debug(f"mirroring buckets: {self._buckets}")
        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(
                f"backup_minio_{bucket}", default_status_level="NOTIFY"
            )
            mc_commands.set_reporter(bucket_report)
            mc_commands.backup_bucket(bucket)
            bucket_report.set_status("Done")

        mc_commands.set_reporter(self._report)
        mc_commands.stop_local()

    def task_path_dir_and_archive_item(self) -> tuple[Path, ArchiveItem]:
        """Simple getter.

        Returns:
            tuple[Path, str]: the dir path of Minio and the constant 'minio'
        """
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.ERROR)
