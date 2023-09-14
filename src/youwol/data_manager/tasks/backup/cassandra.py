"""Main class for the backup task of cassandra."""
# standard library
from pathlib import Path

# typing
from typing import Any

# application services
from youwol.data_manager.services.cqlsh_commands import CqlshCommands
from youwol.data_manager.services.reporting import Report

# relative
from ...configuration import ArchiveItem
from ..common import CommonCassandra, OnPathDirMissing


class Cassandra(CommonCassandra):
    """Subtask for backup cassandra.

    Dump the keyspaces DDL and the tables data in CSV format.
    """

    def __init__(
        self,
        report: Report,
        path_work_dir: Path,
        cqlsh_commands: CqlshCommands,
        keyspaces: list[str],
        tables: list[str],
    ):
        """Simple Constructor.

        Will call CommonCassandra __init__ with path_work_dir, cqlsh_commands, keyspaces and tables.

        Args:
            report (Report): the report
            path_work_dir (Path): the working directory path
            cqlsh_commands (CqlshCommands): the cqlsh_commands service
            keyspaces (list[str]): the list of keyspaces
            tables (list[str]): the list of tables
        """
        super().__init__(path_work_dir, cqlsh_commands, keyspaces, tables)
        self._report = report.get_sub_report(
            "BackupCassandra",
            default_status_level="NOTIFY",
            init_status="ComponentInitialized",
        )

    def run(self) -> None:
        """Run the task."""
        self._report.set_status("Running")

        self._report.debug(f"keyspaces={self._keyspaces}")
        for keyspace in self._keyspaces:
            keyspace_report = self._report.get_sub_report(
                f"backup_ddl_{keyspace}", default_status_level="NOTIFY"
            )
            self._cqlsh_commands.backup_ddl(
                keyspace,
                self._path_cql_ddl_dir(on_missing=OnPathDirMissing.CREATE)
                / f"{keyspace}.cql",
            )
            keyspace_report.set_status("Done")

        self._report.debug(f"tables={self._tables}")
        for table in self._tables:
            table_report = self._report.get_sub_report(
                f"backup_table_{table}", default_status_level="NOTIFY"
            )
            self._cqlsh_commands.backup_table(
                table,
                self._path_cql_data_dir(on_missing=OnPathDirMissing.CREATE)
                / f"{table}.csv",
            )
            table_report.set_status("Done")

        self._report.set_status("Done")

    def task_path_dir_and_archive_item(self) -> tuple[Path, ArchiveItem]:
        """Simple getter.

        Returns:
            tuple[Path, str]: the relative dir for cassandra and 'cql'
        """
        return self._task_path_dir_and_archive_item(OnPathDirMissing.CREATE)

    def metadata(self) -> Any:
        """Simple getter.

        Returns:
            dict: metadata form cqlsh_commands
        """
        return {
            "host": self._cqlsh_commands.show_host(),
            "versions": self._cqlsh_commands.show_version(),
        }
