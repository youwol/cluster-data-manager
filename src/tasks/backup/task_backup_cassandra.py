from pathlib import Path

from services.cqlsh_commands import CqlshCommands
from services.reporting import Report
from tasks.common import OnPathDirMissing, TaskCassandra


class TaskBackupCassandra(TaskCassandra):

    def __init__(self, report: Report,
                 path_work_dir: Path,
                 cqlsh_commands: CqlshCommands,
                 keyspaces: [str],
                 tables: [str]):
        super().__init__(path_work_dir, cqlsh_commands, keyspaces, tables)
        self._report = report.get_sub_report("BackupCassandra", default_status_level="NOTIFY",
                                             init_status="ComponentInitialized")

    def run(self):
        self._report.set_status("Running")

        self._report.debug(f"keyspaces={self._keyspaces}")
        for keyspace in self._keyspaces:
            keyspace_report = self._report.get_sub_report(f"backup_ddl_{keyspace}", default_status_level="NOTIFY")
            self._cqlsh_commands.backup_ddl(
                keyspace,
                self._path_cql_ddl_dir(on_missing=OnPathDirMissing.CREATE) / f"{keyspace}.cql"
            )
            keyspace_report.set_status("Done")

        self._report.debug(f"tables={self._tables}")
        for table in self._tables:
            table_report = self._report.get_sub_report(f"backup_table_{table}", default_status_level="NOTIFY")
            self._cqlsh_commands.backup_table(
                table,
                self._path_cql_data_dir(on_missing=OnPathDirMissing.CREATE) / f"{table}.csv"
            )
            table_report.set_status("Done")

        self._report.set_status("Done")

    def task_path_dir_and_archive_item(self):
        return self._task_path_dir_and_archive_item(OnPathDirMissing.CREATE)

    def metadata(self):
        return {
            "host": self._cqlsh_commands.show_host(),
            "versions": self._cqlsh_commands.show_version()
        }
