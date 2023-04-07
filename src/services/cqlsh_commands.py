import datetime
import subprocess
from pathlib import Path
from typing import Optional

from services.reporting import Report


class CqlInstance:

    def __init__(self, host: Optional[str]):
        self._host = host

    def get_host(self):
        return self._host

    def as_args_array(self):
        return [self._host] if self._host is not None else []


class CqlshCommands:

    def __init__(self, report: Report, cqlsh: str, instance: CqlInstance):
        self._report = report.get_sub_report("CqlshCommands", init_status="InitializingComponent")
        self._cqlsh = cqlsh.split(" ")
        self._instance = instance
        self._report.debug(f"using instance {instance.get_host()}")

    def backup_ddl(self, keyspace: str, path_file: Path):
        report = self._report.get_sub_report(f"backup_ddl_{keyspace}", init_status="in function")
        report.debug(f"will store ddl in {path_file}")
        code, out, err = self.run_command(report, f"CONSISTENCY ALL; DESCRIBE {keyspace};")
        if code == 0:
            path_file.write_text(filter_first_line(out))
            report.set_status("Done")
        else:
            raise RuntimeError(f"Failure: {err}")

    def restore_ddl(self, keyspace: str, path_file: Path, drop_if_exists=False):
        report = self._report.get_sub_report(f"restore_ddl_{keyspace}", init_status="in function")
        report.debug(f"will take ddl from file {path_file}")

        cql_preamble = f"CONSISTENCY ALL;DROP KEYSPACE IF EXISTS {keyspace};" if drop_if_exists else "CONSISTENCY ALL;"

        code, out, err = self.run_command(report, f"{cql_preamble}\n{path_file.read_text('utf8')}")
        if code == 0:
            report.debug("ok")
        elif code == 2:
            msg_idx_token_in_materialized_view = 'InvalidRequest: Error from server: code=2200 [Invalid query] message="Unknown column name detected in CREATE MATERIALIZED VIEW statement: idx_token"'
            err_lines = err.splitlines()
            if all([message.find(msg_idx_token_in_materialized_view) > 0 for message in err_lines]):
                report.warning(f"Ignoring {len(err_lines)} failure(s) '{msg_idx_token_in_materialized_view}'")
            else:
                report.warning(f"ERROR : {err}")
                raise RuntimeError(f"Failure: {err}")
        else:
            raise RuntimeError(f"Failure: {err}")

        report.debug(f"checking keyspace {keyspace}")
        code, out, err = self.run_command(report, f"CONSISTENCY ALL; DESCRIBE {keyspace};")
        if code == 0:
            diff = [line for line in filter_first_line(out).split("\n\n")
                    if line not in path_file.read_text('utf8').split("\n\n")]
            if len(diff) > 0:
                raise RuntimeError(f"keyspace {keyspace} not correctly restored, diff are {diff}")
        else:
            raise RuntimeError(f"Failure {out}")
        report.set_status("Done")

    def backup_table(self, table: str, path_file: Path):
        report = self._report.get_sub_report(f"backup_table_{table}", init_status="in function")
        report.debug(f"will store table data in {path_file}")
        total = self.count_table(report, table)

        count = 0

        last_message_timestamp = datetime.datetime.now().timestamp()
        out = ""

        def on_line(line: str):
            now = datetime.datetime.now().timestamp()
            nonlocal last_message_timestamp
            nonlocal count
            nonlocal out
            count = count + 1
            out = f"{out}{line}"
            if (now - last_message_timestamp) > 1:
                last_message_timestamp = now
                report.debug(f"Copied {count} / {total} lines ")

        self.run_command_with_handler(report, f"CONSISTENCY ALL; COPY {table} TO STDOUT;", on_line=on_line)
        if (count-1) != total:
            raise RuntimeError(f"Wrong count of rows : expected {total}, got {count}")
        path_file.write_text(filter_first_line(out))
        report.set_status("Done")

    def restore_table(self, table: str, path_file: Path, truncate=False):
        report = self._report.get_sub_report(f"restore_table_{table}", init_status="in function")
        report.debug(f"will take data from file {path_file}")

        cql_preamble = f"CONSISTENCY ALL; TRUNCATE {table};" if truncate else "CONSISTENCY ALL;"

        cql = f"{cql_preamble} COPY {table} FROM STDIN;"

        data = path_file.read_text(encoding="utf8")
        total = len(data.splitlines())

        code, out, err = self.run_command(report, cql, data)
        if code != 0:
            raise RuntimeError(f"Failure : {err}")

        actual_total = self.count_table(report, table)

        if total != actual_total:
            raise RuntimeError(f"Expected total row {total}, actual is {actual_total}")

    def count_table(self, report: Report, table: str) -> int:
        report = report.get_sub_report("_count_table", init_status="in function")
        report.debug(f"table={table}")
        code, out, err = self.run_command(report, f"CONSISTENCY ALL;SELECT count(*) FROM {table};")
        if code == 0:
            lines = out.splitlines()
            report.debug(f"lines={lines}")
            count_str = lines[4].strip()
            return int(count_str)
        else:
            raise RuntimeError(f"Failure: {err}")

    def run_command(self, report: Report, cql: str, stdin: Optional[str] = None):
        report = report.get_sub_report("_run_command", init_status="in function")
        args = []
        if stdin is None:
            stdin = cql
        else:
            args = ["-e", cql]
        report.debug(f"cql='{cql}', args='{args}', stdin='{stdin}'")
        result = subprocess.run(
            [*self._cqlsh, *self._instance.as_args_array(), *args],
            input=stdin,
            capture_output=True,
            text=True
        )
        report.debug(f"return_code={result.returncode}")
        report.debug(f"out={result.stdout}")
        report.debug(f"err={result.stderr}")
        return result.returncode, result.stdout, result.stderr,

    def run_command_with_handler(self, report: Report, cql: str, on_line):
        report = report.get_sub_report("_run_command_with_handler", init_status="in function")
        report.debug(f"cql={cql}")
        with subprocess.Popen([*self._cqlsh, *self._instance.as_args_array(), "-e", cql],
                              stdout=subprocess.PIPE) as popen:
            for line in popen.stdout:
                on_line(line.decode('utf8'))

        report.set_status("exit function")


def filter_first_line(text: str):
    lines = text.splitlines(keepends=True)
    return "".join(lines[1:])
