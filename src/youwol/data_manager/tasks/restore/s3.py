"""Main class for restoration subtask of S3."""
# standard library
from pathlib import Path

# application services
from youwol.data_manager.services.mc_commands import McCommands
from youwol.data_manager.services.reporting import Report

# relative
from ...configuration import ArchiveItem
from ..common.s3 import S3 as CommonS3
from ..common.task import OnPathDirMissing


class S3(CommonS3):
    """Restoration subtask for S3.

    Will use mc_commands to mirror local bucket to cluster S3 instance.
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
            overwrite (bool): overwrite behavior when restoring buckets
        """
        super().__init__(path_work_dir, mc_commands, buckets)
        self._report = report.get_sub_report(
            "RestoreS3",
            default_status_level="NOTIFY",
            init_status="ComponentInitialized",
        )

    def run(self) -> None:
        """Run the task."""
        mc_commands = self._mc_commands
        self._report.debug(f"buckets={self._buckets}")

        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(
                f"restore_minio_{bucket}", default_status_level="NOTIFY"
            )
            mc_commands.set_reporter(bucket_report)
            mc_commands.restore_bucket(bucket, remove_existing_bucket=True)
            bucket_report.set_status("Done")

        mc_commands.set_reporter(self._report)
        mc_commands.stop_local()

    def task_path_dir_and_archive_item(self) -> tuple[Path, ArchiveItem]:
        """Simple getter.

        Return:
            tuple[Path, str]: the relative path for Minio and the constant 'minio'
        """
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.ERROR)
