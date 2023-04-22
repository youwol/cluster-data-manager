"""Parent class for S3 tasks."""
from pathlib import Path

from services.mc_commands import McCommands
from .task import OnPathDirMissing, Task


class S3(Task):
    """Parent class for S3 tasks.

    Define relative path for tasks.
    """

    RELATIVE_PATH = "minio"

    def __init__(
        self, path_work_dir: Path, mc_commands: McCommands, buckets: list[str]
    ):
        """Simple constructor.

        Will call Task __init__ with path_work_dir.

        Args:
            path_work_dir (Path): the working directory path
            mc_commands (McCommands): the mc_commands service
            buckets: (list[str]): the list of buckets
        """
        super().__init__(path_work_dir)
        self._mc_commands = mc_commands
        self._buckets = buckets

    def _task_path_dir_and_archive_item(
        self, on_missing: OnPathDirMissing
    ) -> tuple[Path, str]:
        return (
            self._path_dir_maybe_exists(S3.RELATIVE_PATH, on_missing=on_missing),
            S3.RELATIVE_PATH,
        )
