"""Main class and ancillary classes for cqlsh_commands service."""
import datetime
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

from .reporting import Report

MSG_INVALID_REQUEST_COL_IDX_TOKEN = 'InvalidRequest: Error from server: code=2200 [Invalid query] message="Unknown ' \
                                    'column name detected in CREATE MATERIALIZED VIEW statement: idx_token"'


class CqlInstance:
    """Represent the Cassandre host to connect to."""

    def __init__(self, host: Optional[str]):
        """Simple constructor.

        Args:
            host (Optional[str]): the host
        """
        self._host = host

    def get_host(self) -> Optional[str]:
        """Simple getter.

        Returns:
            str: the hostname.
        """
        return self._host

    def as_args_array(self) -> list[str]:
        """Data as an array that can be passed as arguments to a subprocess call.

        Returns:
            [str]: the data split in an array
        """
        return [self._host] if self._host is not None else []


class CqlshCommands:
    """Execute CQL statements, using cqlsh."""

    def __init__(self, report: Report, cqlsh: str, cql_instance: CqlInstance):
        """Simple constructor.

        Args:
            report (services.reporting.reporting.Report): the report
            cqlsh (str): the command line for calling cqlsh
            cql_instance (CqlInstance): the cql instance to connect to
        """
        self._report = report.get_sub_report("CqlshCommands", init_status="InitializingComponent")
        self._cqlsh = cqlsh.split(" ")
        self._instance = cql_instance
        self._report.debug(f"using instance {cql_instance.get_host()}")

    def show_host(self) -> str:
        """Run statement 'SHOW HOST;' and return the output.

        Returns:
            str: output of the command
        """
        report = self._report.get_sub_report("show_host", init_status="in function")
        code, out, err = self._run_command(report, "SHOW HOST;")
        if code != 0:
            raise RuntimeError(f"Failure: {err}")

        result = str(out)
        report.set_status(f"Result: {out}")
        return result

    def show_version(self) -> str:
        """Run statement 'SHOW VERSION;' and return the output.

        Returns:
            str: output of the command
        """
        report = self._report.get_sub_report("show_version", init_status="in function")
        code, out, err = self._run_command(report, "SHOW VERSION;")
        if code != 0:
            raise RuntimeError(f"Failure: {err}")

        result = str(out)
        report.set_status(f"Result: {out}")
        return result

    def backup_ddl(self, keyspace: str, path_file: Path) -> None:
        """Dump the Data Description Langage script for a keyspace into a file.

        Run statement 'DESCRIBE <keyspace>;' with full consistency and write process stdout into the file.

        Notes:
            Since it is the output of the 'CONSISTENCY ALL' statement, the first line of output is removed
            before writing to file.

        Args:
            keyspace (str): name of the keyspace.
            path_file (Path): output file.
        """
        report = self._report.get_sub_report(f"backup_ddl_{keyspace}", init_status="in function")
        report.debug(f"will store ddl in {path_file}")
        code, out, err = self._run_command(report, f"CONSISTENCY ALL; DESCRIBE {keyspace};")
        if code != 0:
            raise RuntimeError(f"Failure: {err}")

        path_file.write_text("".join(out.splitlines(keepends=True)[1:]))
        report.set_status("Done")

    def restore_ddl(self, keyspace: str, path_file: Path, drop_if_exists: bool = False) -> None:
        """Execute a Data Description Langage script from a file.

        Run statements from a file to restore a keyspace, and check the keyspace restored.

        If drop_if_exists is True, the keyspace is dropped before executing DDL.

        If process exit with code 2, lines matching MSG_INVALID_REQUEST_COL_IDX_TOKEN in stderr are ignored
        while any other error is fatal.

        Once the DDL script has been executed, the command 'DESCRIBE <keyspace>' is run again and its output is check
        against the executed script.

        Args:
            keyspace (str): name of the keyspace
            path_file (Path): input file
            drop_if_exists (bool): if provided and True, drop keyspace before executing DDL script.
        """
        report = self._report.get_sub_report(f"restore_ddl_{keyspace}", init_status="in function")
        report.debug(f"will take ddl from file {path_file}")

        cql_preamble = f"CONSISTENCY ALL;DROP KEYSPACE IF EXISTS {keyspace};" if drop_if_exists else "CONSISTENCY ALL;"

        code, out, err = self._run_command(report, f"{cql_preamble}\n{path_file.read_text('utf8')}")
        if code == 0:
            report.debug("ok")
        elif code == 2:
            err_lines = err.splitlines()
            if all(message.find(MSG_INVALID_REQUEST_COL_IDX_TOKEN) > 0 for message in err_lines):
                report.warning(f"Ignoring {len(err_lines)} failure(s) '{MSG_INVALID_REQUEST_COL_IDX_TOKEN}'")
            else:
                report.fatal(f"ERROR : {err}")
                raise RuntimeError(f"Failure: {err}")
        else:
            raise RuntimeError(f"Failure: {err}")

        # Check created keyspace against DDL in file
        report.debug(f"checking keyspace {keyspace}")
        code, out, err = self._run_command(report, f"CONSISTENCY ALL; DESCRIBE {keyspace};")
        if code == 0:
            diff = [line for line in "".join(out.splitlines(keepends=True)[1:]).split("\n\n") if
                    line not in path_file.read_text('utf8').split("\n\n")]
            if len(diff) > 0:
                raise RuntimeError(f"keyspace {keyspace} not correctly restored, diff are {diff}")
        else:
            raise RuntimeError(f"Failure {out}")
        report.set_status("Done")

    def backup_table(self, table: str, path_file: Path) -> None:
        """Dump table data in CSV format into a file.

        Run statement 'COPY <table> TO STDOUT;' with full consistency and write process stdout into the file.

        Once statement has been executed, the number of lines in output is checked against the number of row in the
        table.

        Notes:
            Since it is the output of the 'CONSISTENCY ALL' statement, the first line of output is not counted.

        Args:
            table (str): name of the table.
            path_file (Path): output file.
        """
        report = self._report.get_sub_report(f"backup_table_{table}", init_status="in function")
        report.debug(f"will store table data in {path_file}")

        # Expected nb of line in output
        total = self._count_table(report, table)

        out = ""
        # Count the lines in output
        count = 0
        last_message_timestamp = datetime.datetime.now().timestamp()

        def on_line(line: str) -> None:
            now = datetime.datetime.now().timestamp()
            nonlocal last_message_timestamp
            nonlocal count
            nonlocal out
            count = count + 1
            out = f"{out}{line}"
            if (now - last_message_timestamp) > 1:
                last_message_timestamp = now
                report.debug(f"Copied {count} / {total} lines ")

        self._run_command_with_handler(report, f"CONSISTENCY ALL; COPY {table} TO STDOUT;", on_line=on_line)

        # Check nb of lines, minus the first line (output of 'CONSISTENCY ALL;'.
        if (count - 1) != total:
            raise RuntimeError(f"Wrong count of rows : expected {total}, got {count}")

        path_file.write_text("".join(out.splitlines(keepends=True)[1:]))
        report.set_status("Done")

    def restore_table(self, table: str, path_file: Path, truncate: bool = False) -> None:
        """Restore table data from a file in CSV format.

        Run statement 'COPY <table> FROM STDIN' with full consistency, sending file content to process stdin.

        If truncate is True, the statement 'TRUNCATE <table>' is run before copying data.

        Once the statemente has been executed, the number of row in the table is checked against the number of line
         in the file.

        Args:
            table (str): name of the table.
            path_file (Path): input file.
            truncate (bool): if provided and True, the table will be truncated before copying data
        """
        report = self._report.get_sub_report(f"restore_table_{table}", init_status="in function")
        report.debug(f"will take data from file {path_file}")

        cql_preamble = f"CONSISTENCY ALL; TRUNCATE {table};" if truncate else "CONSISTENCY ALL;"

        cql = f"{cql_preamble} COPY {table} FROM STDIN;"

        data = path_file.read_text(encoding="utf8")
        total = len(data.splitlines())

        code, _, err = self._run_command(report, cql, data)
        if code != 0:
            raise RuntimeError(f"Failure : {err}")

        actual_total = self._count_table(report, table)

        if total != actual_total:
            raise RuntimeError(f"Expected total row {total}, actual is {actual_total}")

    def _count_table(self, report: Report, table: str) -> int:
        """Return the number of rows in a table.

        Run statement 'SELECT count(*) FROM <table>' with full consistency, and return the fifth line of the output.

        Args:
            report (Report): logger for that action.
            table (str): name of the table.
        """
        report = report.get_sub_report("_count_table", init_status="in function")
        report.debug(f"table={table}")
        code, out, err = self._run_command(report, f"CONSISTENCY ALL;SELECT count(*) FROM {table};")
        if code != 0:
            raise RuntimeError(f"Failure: {err}")

        lines = out.splitlines()
        report.debug(f"lines={lines}")
        count_str = lines[4].strip()
        return int(count_str)

    def _run_command(self, report: Report, cql: str, stdin: Optional[str] = None) -> tuple[int, Any, Any]:
        report = report.get_sub_report("__run_command", init_status="in function")
        args = []
        if stdin is None:
            stdin = cql
        else:
            args = ["-e", cql]
        report.debug(f"cql='{cql}', args='{args}', stdin='{stdin}'")
        result = subprocess.run([*self._cqlsh, *self._instance.as_args_array(), *args], input=stdin,
                                capture_output=True, text=True, check=False)
        report.debug(f"return_code={result.returncode}")
        report.debug(f"out={result.stdout}")
        report.debug(f"err={result.stderr}")
        return result.returncode, result.stdout, result.stderr

    def _run_command_with_handler(self, report: Report, cql: str, on_line: Callable[[str], None]) -> None:
        report = report.get_sub_report("__run_command_with_handler", init_status="in function")
        report.debug(f"cql={cql}")
        with subprocess.Popen([*self._cqlsh, *self._instance.as_args_array(), "-e", cql],
                              stdout=subprocess.PIPE) as popen:
            if popen.stdout is None:
                msg = "no stdout piping when running command"
                report.fatal(msg)
                raise RuntimeError(msg)

            for line in popen.stdout:
                on_line(line.decode('utf8'))

        report.set_status("exit function")
