"""Main class for restoration subtask of S3."""
from pathlib import Path

from services.mc_commands import McCommands
from services.reporting import Report
from tasks.common import OnPathDirMissing, TaskS3


class TaskRestoreS3(TaskS3):
    """Restoration subtask for S3.

    Will use mc_commands to mirror local bucket to cluster S3 instance.
    """
    def __init__(self, report: Report, path_work_dir: Path, mc_commands: McCommands, buckets: [str], overwrite: bool):
        super().__init__(path_work_dir, mc_commands, buckets)
        self._overwrite = overwrite
        self._report = report.get_sub_report("RestoreS3", default_status_level="NOTIFY",
                                             init_status="ComponentInitialized")

    def run(self):
        """Run the task."""
        mc_commands = self._mc_commands
        self._report.debug(f"buckets={self._buckets}")

        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(f"restore_minio_{bucket}", default_status_level="NOTIFY")
            mc_commands.set_reporter(bucket_report)
            mc_commands.restore_bucket(bucket, self._overwrite)
            bucket_report.set_status("Done")

        mc_commands.set_reporter(self._report)
        mc_commands.stop_local()

    def task_path_dir_and_archive_item(self):
        """Simple getter.

        Return:
            tuple[Path, str]: the relative path for Minio and the constant 'minio'
        """
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.ERROR)
