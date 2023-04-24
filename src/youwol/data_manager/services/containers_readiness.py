"""Main class and ancillary classes to probe containers readiness."""
# standard library
import datetime
import time
import urllib.request

from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError

# relative
from .mc_commands import S3Instance
from .reporting import Report


@dataclass(frozen=True, kw_only=True)
class Probe:
    """Base class for the probes."""

    report: Report

    def __post_init__(self):
        """Set up sub report with child name"""
        object.__setattr__(
            self,
            "report",
            self.report.get_sub_report(
                type(self).__name__, init_status="ComponentInitialized"
            ),
        )

    def probe(self) -> bool:
        """Call child method child.probe."""
        report = self.report.get_sub_report("probe", init_status="in function")
        result = self._probe()
        report.notify(f"result: {result}")
        return result

    def _probe(self) -> bool:
        """Abstract method."""
        raise NotImplementedError("Abstract method")


@dataclass(frozen=True, kw_only=True)
class ProbeKeycloak(Probe):
    """Probe for the keycloak container."""

    path_keycloak_status_file: Path

    def _probe(self) -> bool:
        """Probe the keycloak container.

        Will check if the content of the status file is not 'SETUP'

        Returns:
            bool: True if the status file is not 'SETUP' (striped)
        """
        report = self.report.get_sub_report(task="_probe", init_status="in function")
        status = self.path_keycloak_status_file.read_text("UTF-8").strip()
        report.notify(
            f"status file {self.path_keycloak_status_file} content is {status}"
        )
        # TODO: define a constant, shared with setup task
        return status != "SETUP"


@dataclass(frozen=True, kw_only=True)
class ProbeMinio(Probe):
    """Probe for the minio container."""

    s3_instance: S3Instance

    def _probe(self) -> bool:
        """Probe the minio container.

        Will call the health live URL.

        Returns:
            bool: True if getting the health live URL has status code 200
        """
        report = self.report.get_sub_report(task="_probe", init_status="in function")
        try:
            with urllib.request.urlopen(self.s3_instance.health_live_url) as resp:
                status = resp.status
                report.notify(
                    f"GET {self.s3_instance.health_live_url} response with status {status}"
                )
                return status == 200
        except URLError as error:
            report.notify(
                f"Failed to open URL {self.s3_instance.health_live_url} : {error}"
            )
            return False


@dataclass(frozen=True, kw_only=True)
class ContainersReadiness:
    """Service container readiness."""

    report: Report
    probes: list[Probe]
    wait_timeout: int = 300
    interval: int = 5

    def wait(self):
        """Wait for all probes to success."""
        give_up_at = datetime.datetime.now().timestamp() + self.wait_timeout
        success = all(probe.probe() for probe in self.probes)
        while not success:
            time.sleep(self.interval)
            if datetime.datetime.now().timestamp() > give_up_at:
                raise RuntimeError(f"Probing failed after {self.wait_timeout} seconds")

            success = all(probe.probe() for probe in self.probes)
