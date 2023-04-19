"""Parent class for S3 tasks."""
from pathlib import Path

from services.mc_commands import McCommands
from .task import OnPathDirMissing, Task


class TaskS3(Task):
    """Parent class for S3 tasks.

    Define relative path for tasks.
    """
    RELATIVE_PATH = "minio"

    def __init__(self, path_work_dir: Path, mc_commands: McCommands, buckets: [str]):
        super().__init__(path_work_dir)
        self._mc_commands = mc_commands
        self._buckets = buckets

    def _task_path_dir_and_archive_item(self, on_missing: OnPathDirMissing):
        return self._path_dir_maybe_exists(TaskS3.RELATIVE_PATH, on_missing=on_missing), TaskS3.RELATIVE_PATH
