"""Main class and ancillary classes for service mc_commands."""
# standard library
import datetime
import json
import subprocess
import time

from dataclasses import dataclass, field
from pathlib import Path

# typing
from typing import Any, Callable, Optional

# relative
from .reporting import Report


@dataclass(frozen=True)
class S3Credentials:
    """Represent credentials for S3."""

    access_key: str
    secret_key: str


@dataclass(frozen=True, kw_only=True)
class S3Instance:
    """Represent a S3 service to connect to."""

    credentials: S3Credentials
    host: str
    tls: bool = True
    port: int = 9000
    base_url: str = field(init=False)
    health_live_url: str = field(init=False)

    def __post_init__(self) -> None:
        """Construct URL from initial attributes.

        Notes:
            Use object.__setattr__() to bypass @dataclass(frozen=True)
        """
        base_url = f"http{'s' if self.tls else ''}://{self.host}:{self.port}"
        object.__setattr__(self, "base_url", base_url)
        health_live_url = f"{base_url}/minio/health/live"
        object.__setattr__(self, "health_live_url", health_live_url)


@dataclass(frozen=True, init=False)
class MinioLocalInstance(S3Instance):
    """Represent a local S3 service to connect, with host hardcoded to localhost."""

    def __init__(self, access_key: str, secret_key: str, port: int):
        """Simple constructor.

        Will call S3Instance __init__ with an S3Credentials (from access_key and secret_key), host set to
        'localhost', tls set to False and port

        Args:
            access_key (str): the local credential access_key
            secret_key (str): the local credential secret_key
            port (int): the local minio instance port
        """
        super().__init__(
            credentials=S3Credentials(access_key=access_key, secret_key=secret_key),
            host="localhost",
            tls=False,
            port=port,
        )


@dataclass(frozen=True, kw_only=True)
class MinioClientPaths:
    """Represent the paths for a Minio client (mc) binary."""

    path_bin: Path
    path_config: Path


class McCommands:
    """Execute S3 commands, using Minio client (mc)."""

    ALIAS_LOCAL = "local"

    ALIAS_CLUSTER = "cluster"

    def __init__(
        self,
        report: Report,
        mc_paths: MinioClientPaths,
        minio_instance: MinioLocalInstance,
        s3_instance: S3Instance,
    ):
        """Simple constructor.

        Args:
            report (Report): the report
            mc_paths (MinioClientPaths): the path to mc binary and the path to mc config directory
            minio_instance: the local minio instance
            s3_instance: the cluster S3 instance
        """
        self._report = report.get_sub_report(
            task="McCommands", init_status="InitializingComponent"
        )
        self._path_mc = mc_paths.path_bin
        self._report.debug(f"using binary {self._path_mc}")
        self._path_mc_config = mc_paths.path_config
        self._report.debug(f"using config {self._path_mc_config}")
        self._local = minio_instance
        self._cluster = s3_instance
        self._aliases_setup_done = False
        self._report.set_status("ComponentInitialized")

    def cluster_url(self) -> str:
        """Simple getter.

        Returns:
            str: the cluster instance URL.
        """
        return self._cluster.base_url

    def cluster_info(self) -> Any:
        """Return information about the cluster instance.

        Execute 'mc admin info' and return the JSON output as an object.

        Returns:
            Any: admin infos for the cluster.
        """
        report = self._report.get_sub_report("admin_info", init_status="in function")
        self._need_aliases()

        result = {}

        def on_success(json_doc: Any) -> None:
            nonlocal result
            result = json_doc["info"]

        self._run_command(
            report, "admin", "info", McCommands.ALIAS_CLUSTER, on_success=on_success
        )
        return result

    def _setup_aliases(self) -> None:
        self._mc_alias(McCommands.ALIAS_LOCAL, self._local)
        self._mc_alias(McCommands.ALIAS_CLUSTER, self._cluster)
        self._aliases_setup_done = True

    def _need_aliases(self) -> None:
        if not self._aliases_setup_done:
            self._setup_aliases()

    def set_reporter(self, report: Report) -> None:
        """TODO: to be removed."""
        self._report = report.get_sub_report(
            task="McCommands", init_status=report.get_status()
        )

    def backup_bucket(self, bucket: str) -> None:
        """Mirror a cluster instance bucket locally.

        Args:
            bucket (str): the bucket name.
        """
        self._need_aliases()
        report = self._report.get_sub_report(
            f"backup_{bucket}", init_status="in function"
        )
        source = f"{McCommands.ALIAS_CLUSTER}/{bucket}"
        target = f"{McCommands.ALIAS_LOCAL}/{bucket}"

        report.set_status("CreateLocalBucket")
        self._run_command(report, "mb", "--ignore-existing", target)

        report.set_status("Transfert")
        self._mirror_buckets(report, source, target)

        report.set_status("exit function")

    def restore_bucket(self, bucket: str, remove_existing_bucket: bool = False) -> None:
        """Mirror a local bucket into the cluster instance.

        If remove_existing_bucket is provided and True, the cluster instance bucket will be removed first.

        Args:
            bucket (str): the bucket name.
            remove_existing_bucket (bool): if provided and True, remove the cluster bucket before mirroring.
        """
        self._need_aliases()
        report = self._report.get_sub_report("restore", init_status="in function")
        source = f"{McCommands.ALIAS_LOCAL}/{bucket}"
        target = f"{McCommands.ALIAS_CLUSTER}/{bucket}"

        if remove_existing_bucket:
            self._run_command(report, "rb", "--force", target)

        report.set_status("CreateClusterBucket")
        self._run_command(report, "mb", target)

        report.set_status("Transfert")
        self._mirror_buckets(report, source, target)

        report.set_status("exit function")

    def stop_local(self) -> None:
        """Stop the local minio instance."""
        self._need_aliases()
        report = self._report.get_sub_report("stop_local", init_status="in function")
        self._run_command(report, "admin", "service", "stop", McCommands.ALIAS_LOCAL)
        report.set_status("exit function")

    def _mirror_buckets(self, report: Report, source: str, target: str) -> None:
        self._need_aliases()
        report = report.get_sub_report("MirrorBucket", init_status="in function")

        report.set_status("DiskUsageSourceBucket")
        source_bucket_objects, source_bucket_size = self._du_bucket(report, source)
        report.notify(
            f"source bucket : {source_bucket_objects} objects / {source_bucket_size} bytes"
        )

        last_message_timestamp = datetime.datetime.now().timestamp()

        def on_success_mirror(json_doc: Any) -> None:
            # report.debug(f"json={json}")
            nonlocal last_message_timestamp
            now = datetime.datetime.now().timestamp()
            if "target" in json_doc and (now - last_message_timestamp > 5):
                last_message_timestamp = now
                transferred_objects = json_doc["totalCount"]
                report.debug(
                    f"transferred {transferred_objects} objects on {source_bucket_objects}"
                )

        report.set_status("Transfert")
        self._run_command(
            report,
            "mirror",
            "--overwrite",
            "--preserve",
            "--remove",
            source,
            target,
            on_success=on_success_mirror,
        )
        report.notify("Done")

        report.set_status("VerifyTargetBucket")

        target_bucket_objects, target_bucket_size = self._du_bucket(report, target)
        if (
            source_bucket_objects != target_bucket_objects
            or source_bucket_size != target_bucket_size
        ):
            time.sleep(5)
            target_bucket_objects, target_bucket_size = self._du_bucket(report, target)
            if (
                source_bucket_objects != target_bucket_objects
                or source_bucket_size != target_bucket_size
            ):
                msg = (
                    f"Mirror {source} to {target} failed:"
                    f" expected {source_bucket_objects} / {source_bucket_size}"
                    f" actual {target_bucket_objects} / {target_bucket_size}"
                )
                report.fatal(msg)
                raise RuntimeError(msg)

        report.set_status("exit function")

    def _du_bucket(self, report: Report, bucket: str) -> tuple[int, int]:
        bucket_size = 0
        bucket_objects = 0

        def on_success_du(json_doc: Any) -> None:
            nonlocal bucket_size
            nonlocal bucket_objects
            report.debug(f"json={json_doc}")
            bucket_size = json_doc["size"]
            bucket_objects = json_doc["objects"]

        self._run_command(report, "du", "--versions", bucket, on_success=on_success_du)
        return bucket_objects, bucket_size

    def du_cluster_bucket(self, bucket: str) -> tuple[int, int]:
        """Run disk usage for cluster bucket.

        Args:
            bucket (str): the bucket name
        Returns:
            tuple[str, str]: the number of objects and the total size
        """
        report = self._report.get_sub_report(
            f"du_cluster_bucket_{bucket}", init_status="in function"
        )
        result = self._du_bucket(report, f"{McCommands.ALIAS_CLUSTER}/{bucket}")
        report.debug("done")
        return result

    def _mc_alias(self, alias: str, instance: S3Instance) -> None:
        report = self._report.get_sub_report(
            f"_mc_alias_{alias}", init_status="in function"
        )
        self._run_command(
            report,
            "alias",
            "set",
            alias,
            instance.base_url,
            instance.credentials.access_key,
            instance.credentials.secret_key,
        )
        report.set_status("exit function")

    def _run_command(
        self,
        report: Report,
        *args: str,
        on_success: Optional[Callable[[Any], None]] = None,
    ) -> None:
        report = report.get_sub_report("_run_command", init_status="in function")
        report.debug(f"args={args}")
        with subprocess.Popen(
            [self._path_mc, "--json", "--config-dir", self._path_mc_config, *args],
            stdout=subprocess.PIPE,
        ) as popen:
            if popen.stdout is None:
                msg = "no stdout piping when running command"
                report.fatal(msg)
                raise RuntimeError(msg)
            for line in popen.stdout:
                # report.debug(f"line={line}")
                json_doc = json.loads(line)
                status = json_doc["status"]
                if status == "error":
                    report.fatal(f"{line!r}")
                    raise RuntimeError(
                        f"failure when running mc command : {json_doc['error']}"
                    )
                if status == "success":
                    if on_success is not None:
                        on_success(json_doc)
                else:
                    raise RuntimeError(f"Unknown status in mc output : {line!r}")

        report.set_status("exit function")
