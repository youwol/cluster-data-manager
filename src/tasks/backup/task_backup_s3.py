from pathlib import Path

from services.mc_commands import McCommands
from services.reporting import Report
from tasks.common import TaskS3, OnPathDirMissing


class TaskBackupS3(TaskS3):
    RELATIVE_PATH = "minio"

    def __init__(self, report: Report, path_work_dir: Path, mc_commands: McCommands, buckets: [str]):
        super().__init__(report, path_work_dir, mc_commands, buckets)
        self._report = report.get_sub_report("BackupS3", default_status_level="NOTIFY",
                                             init_status="ComponentInitialized")

    def run(self):
        mc_commands = self._mc_commands
        self._report.debug(f"buckets={self._buckets}")

        for bucket in self._buckets:
            bucket_report = self._report.get_sub_report(f"backup_minio_{bucket}", default_status_level="NOTIFY")
            mc_commands.set_reporter(bucket_report)
            mc_commands.backup_bucket(bucket)
            bucket_report.set_status("Done")

        mc_commands.set_reporter(self._report)
        mc_commands.stop_local()

    def task_path_dir_and_archive_item(self):
        return self._task_path_dir_and_archive_item(on_missing=OnPathDirMissing.ERROR)
