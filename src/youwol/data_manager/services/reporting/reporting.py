# standard library
import datetime

from pathlib import Path

# typing
from typing import List, Optional


class WithStatus:
    def get_status(self) -> str:
        raise NotImplementedError("WithStatus is abstract")

    def get_parents_tasks(self) -> list[str]:
        raise NotImplementedError("WithStatus is abstract")


class ReportHandler:
    def set_current_report(self, report: WithStatus):
        raise NotImplementedError("ReportHandler is abstract")

    def notify(self, report: WithStatus, msg: str = ""):
        raise NotImplementedError("ReportHandler is abstract")

    def debug(self, report: WithStatus, msg: str = ""):
        raise NotImplementedError("ReportHandler is abstract")

    def warning(self, report: WithStatus, msg: str = ""):
        raise NotImplementedError("ReportHandler is abstract")

    def fatal(self, report: WithStatus, msg: str = ""):
        raise NotImplementedError("ReportHandler is abstract")


class Report(WithStatus):
    def __init__(
        self,
        init_status: str,
        reporting: ReportHandler,
        task: str,
        default_status_level: str = "DEBUG",
        parents_tasks: Optional[list[str]] = None,
    ):
        self._tasks = [*(parents_tasks if parents_tasks is not None else []), task]
        self._reporting = reporting
        self._status = ""
        self._default_status_level = default_status_level
        self.set_status(init_status)

    def get_status(self) -> str:
        return self._status

    def set_status(self, status: str, level: Optional[str] = None):
        self._status = status
        level = self._default_status_level if level is None else level
        if level == "NOTIFY":
            self._reporting.notify(self)
        if level == "DEBUG":
            self._reporting.debug(self)

    def get_parents_tasks(self):
        return self._tasks

    def notify(self, msg: str) -> None:
        self._reporting.notify(self, msg)

    def debug(self, msg: str) -> None:
        self._reporting.debug(self, msg)

    def warning(self, msg: str) -> None:
        self._reporting.warning(self, msg)

    def fatal(self, msg: str) -> None:
        self._reporting.fatal(self, msg)

    def get_sub_report(
        self,
        task: str,
        init_status: str = "Starting",
        default_status_level: str = "DEBUG",
    ):
        return Report(
            init_status=init_status,
            reporting=self._reporting,
            task=task,
            parents_tasks=self._tasks,
            default_status_level=default_status_level,
        )


class Reporting(ReportHandler):
    def __init__(self, path_log_file: Path, initial_task: str):
        self._path_log_file = path_log_file
        self._root_report = Report(
            init_status="Starting",
            reporting=self,
            task=initial_task,
            default_status_level="NOTIFY",
        )
        self._current_report = self._root_report
        self.set_current_report(self._root_report)

    def set_current_report(self, report: WithStatus):
        self._current_report = report

    def get_root_report(self) -> Report:
        return self._root_report

    def notify(self, report: WithStatus, msg: str = ""):
        self._write_log(
            level=" NOTIFY",
            tasks=report.get_parents_tasks(),
            status=report.get_status(),
            msg=msg,
        )

    def debug(self, report: WithStatus, msg: str = ""):
        self._write_log(
            level="  DEBUG",
            tasks=report.get_parents_tasks(),
            status=report.get_status(),
            msg=msg,
        )

    def warning(self, report: WithStatus, msg: str = ""):
        self._write_log(
            level="WARNING",
            tasks=report.get_parents_tasks(),
            status=report.get_status(),
            msg=msg,
        )

    def fatal(self, report: WithStatus, msg: str = ""):
        self._write_log(
            level="  FATAL",
            tasks=report.get_parents_tasks(),
            status=report.get_status(),
            msg=msg,
        )

    def _write_log(self, level: str, tasks: List[str], status: str, msg: str):
        timestamp = datetime.datetime.now()
        tasks_str = ">".join(tasks)
        msg_str = f" : {msg}" if msg != "" else ""
        msg = f"{timestamp} {level} ({tasks_str})[{status}]{msg_str}"
        print(msg, flush=True)
        self._path_log_file.open("a").write(f"{msg}\n")

    def start_thread(self):
        pass

    def stop_thread(self):
        pass
