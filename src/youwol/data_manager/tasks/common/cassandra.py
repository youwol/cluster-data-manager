"""Parent class for cassandra tasks."""
# standard library
from pathlib import Path

# application services
from youwol.data_manager.services.cqlsh_commands import CqlshCommands

# relative
from .task import OnPathDirMissing, Task


class Cassandra(Task):
    """Parent class for cassandra tasks.

    Define relative paths for the tasks.
    """

    RELATIVE_PATH = "cql"
    RELATIVE_PATH_SCHEMA = "cql/schema"
    RELATIVE_PATH_DATA = "cql/data"

    def __init__(
        self,
        path_work_dir: Path,
        cqlsh_commands: CqlshCommands,
        keyspaces: list[str],
        tables: list[str],
    ):
        """Simple constructor.

        Will call Task __init__ with path_work_dir.

        Args:
            path_work_dir (Path): the working directory path
            cqlsh_commands (CqlshCommands): the cqlsh_commands service
            keyspaces (list[str]): the list of keyspaces
            tables (list[str]): the list of tables
        """
        super().__init__(path_work_dir)
        self._cqlsh_commands = cqlsh_commands
        self._keyspaces = keyspaces
        self._tables = tables

    def _task_path_dir_and_archive_item(
        self, on_missing: OnPathDirMissing
    ) -> tuple[Path, str]:
        return (
            self._path_dir_maybe_exists(Cassandra.RELATIVE_PATH, on_missing=on_missing),
            Cassandra.RELATIVE_PATH,
        )

    def _path_cql_ddl_dir(self, on_missing: OnPathDirMissing) -> Path:
        return self._path_dir_maybe_exists(
            Cassandra.RELATIVE_PATH_SCHEMA, on_missing=on_missing
        )

    def _path_cql_data_dir(self, on_missing: OnPathDirMissing) -> Path:
        return self._path_dir_maybe_exists(
            Cassandra.RELATIVE_PATH_DATA, on_missing=on_missing
        )
