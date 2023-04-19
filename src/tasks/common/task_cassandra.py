"""Parent class for cassandra tasks."""
from pathlib import Path

from services.cqlsh_commands import CqlshCommands
from .task import OnPathDirMissing, Task


class TaskCassandra(Task):
    """Parent class for cassandra tasks.

    Define relative paths for the tasks.
    """
    RELATIVE_PATH = "cql"
    RELATIVE_PATH_SCHEMA = "cql/schema"
    RELATIVE_PATH_DATA = "cql/data"

    def __init__(self, path_work_dir: Path, cqlsh_commands: CqlshCommands, keyspaces: [str], tables: [str]):
        super().__init__(path_work_dir)
        self._cqlsh_commands = cqlsh_commands
        self._keyspaces = keyspaces
        self._tables = tables

    def _task_path_dir_and_archive_item(self, on_missing: OnPathDirMissing):
        return self._path_dir_maybe_exists(TaskCassandra.RELATIVE_PATH,
                                           on_missing=on_missing), TaskCassandra.RELATIVE_PATH

    def _path_cql_ddl_dir(self, on_missing: OnPathDirMissing):
        return self._path_dir_maybe_exists(TaskCassandra.RELATIVE_PATH_SCHEMA, on_missing=on_missing)

    def _path_cql_data_dir(self, on_missing: OnPathDirMissing):
        return self._path_dir_maybe_exists(TaskCassandra.RELATIVE_PATH_DATA, on_missing=on_missing)
