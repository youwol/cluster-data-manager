"""Main class for subtask restoration of cassandra."""
from pathlib import Path

from services.cqlsh_commands import CqlshCommands
from services.reporting import Report
from ..common.cassandra import Cassandra as CommonCassandra
from ..common.task import OnPathDirMissing


class Cassandra(CommonCassandra):
    """Restoration subtask for cassandra.

    Use cqlsh_commands to restore keyspaces from DDL files and tables data from CSV files.
    """

    def __init__(
        self,
        report: Report,
        path_work_dir: Path,
        cqlsh_commands: CqlshCommands,
        keyspaces: list[str],
        tables: list[str],
        overwrite: bool,
    ):
        """Simple Constructor.

        Will call CommonCassandra __init__ with path_work_dir, cqlsh_commands, keyspaces and tables.

        Args:
            report (Report): the report
            path_work_dir (Path): the working directory path
            cqlsh_commands (CqlshCommands): the cqlsh_commands service
            keyspaces (list[str]): the list of keyspaces
            tables (list[str]): the list of tables
            overwrite (bool): overwrite behavior when restoring keyspaces and tables
        """
        super().__init__(path_work_dir, cqlsh_commands, keyspaces, tables)
        self._overwrite = overwrite
        self._report = report.get_sub_report(
            "RestoreCassandra",
            default_status_level="NOTIFY",
            init_status="ComponentInitialized",
        )

    def run(self) -> None:
        """Run the task."""
        self._report.set_status("Running")

        self._report.debug(f"keyspaces={self._keyspaces}")
        for keyspace in self._keyspaces:
            keyspace_report = self._report.get_sub_report(
                f"restore_ddl_{keyspace}", default_status_level="NOTIFY"
            )
            self._cqlsh_commands.restore_ddl(
                keyspace,
                self._path_cql_ddl_dir(on_missing=OnPathDirMissing.ERROR)
                / f"{keyspace}.cql",
                self._overwrite,
            )
            keyspace_report.set_status("Done")

        self._report.debug(f"tables={self._tables}")
        for table in self._tables:
            table_report = self._report.get_sub_report(
                f"restore_table_{table}", default_status_level="NOTIFY"
            )
            self._cqlsh_commands.restore_table(
                table,
                self._path_cql_data_dir(on_missing=OnPathDirMissing.ERROR)
                / f"{table}.csv",
                self._overwrite,
            )
            table_report.set_status("Done")

        self._report.set_status("Done")

    def task_path_dir_and_archive_item(self) -> tuple[Path, str]:
        """Simple getter.

        Returns:
            tuple[Path, str]: the relative path for cassandra and 'cql'
        """
        return self._task_path_dir_and_archive_item(OnPathDirMissing.ERROR)
