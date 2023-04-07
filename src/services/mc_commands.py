import datetime
import json
import subprocess
from pathlib import Path
from typing import Any

from services.reporting import Report


def default_on_error(json: Any):
    raise RuntimeError(f"error {json}")


def default_on_success(json: Any):
    pass


class S3Instance:

    def __init__(self, access_key: str, secret_key: str, host: str, tls: bool = True, port: int = "9000"):
        self._access_key = access_key
        self._secret_key = secret_key
        self._host = host
        self._tls = tls
        self._port = port

    def url(self):
        return f"http{'s' if self._tls else ''}://{self._host}:{self._port}"

    def access_key(self):
        return self._access_key

    def secret_key(self):
        return self._secret_key


class MinioLocalInstance(S3Instance):
    def __init__(self, access_key, secret_key, tls: bool, port: int):
        super().__init__(access_key, secret_key, host="localhost", tls=tls, port=port)


class McCommands:
    ALIAS_LOCAL = "local"

    ALIAS_CLUSTER = "cluster"

    def __init__(self, report: Report, path_mc: Path, path_mc_config: Path, local: MinioLocalInstance,
                 cluster: S3Instance):
        self._report = report.get_sub_report(task="McCommands", init_status="InitializingComponent")
        self._path_mc = path_mc
        self._report.debug(f"using binary {self._path_mc}")
        self._path_mc_config = path_mc_config
        self._report.debug(f"using config {self._path_mc_config}")
        self._local = local
        self._cluster = cluster
        self._aliases_setup_done = False
        self._report.set_status("ComponentInitialized")

    def _setup_aliases(self):
        self._mc_alias(McCommands.ALIAS_LOCAL, self._local)
        self._mc_alias(McCommands.ALIAS_CLUSTER, self._cluster)
        self._aliases_setup_done = True

    def _need_aliases(self):
        if not self._aliases_setup_done:
            self._setup_aliases()

    def set_reporter(self, report: Report):
        self._report = report.get_sub_report(task="McCommands", init_status=report.get_status())

    def backup_bucket(self, bucket):
        self._need_aliases()
        report = self._report.get_sub_report(f"backup_{bucket}", init_status="in function")
        source = f"{McCommands.ALIAS_CLUSTER}/{bucket}"
        target = f"{McCommands.ALIAS_LOCAL}/{bucket}"

        report.set_status("CreateLocalBucket")
        self._run_command(report, "mb", "--ignore-existing", target)

        report.set_status("Transfert")
        self._mirror_buckets(report, source, target)

        report.set_status("exit function")

    def restore_bucket(self, bucket, remove_existing_bucket=False):
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

    def stop_local(self):
        self._need_aliases()
        report = self._report.get_sub_report("stop_local", init_status="in function")
        self._run_command(report, "admin", "service", "stop", McCommands.ALIAS_LOCAL)
        report.set_status("exit function")

    def _mirror_buckets(self, report: Report, source: str, target: str):
        self._need_aliases()
        report = report.get_sub_report("MirrorBucket", init_status="in function")

        report.set_status("DiskUsageSourceBucket")
        source_bucket_objects, source_bucket_size = self._du_bucket(report, source)
        report.notify(f"source bucket : {source_bucket_objects} objects / {source_bucket_size} bytes")

        last_message_timestamp = datetime.datetime.now().timestamp()

        def on_success_mirror(json: Any):
            # report.debug(f"json={json}")
            nonlocal last_message_timestamp
            now = datetime.datetime.now().timestamp()
            if 'target' in json and (now - last_message_timestamp > 5):
                last_message_timestamp = now
                transferred_objects = json['totalCount']
                report.debug(f"transferred {transferred_objects} objects on {source_bucket_objects}")

        report.set_status("Transfert")
        self._run_command(report, "mirror", "--overwrite", "--preserve", "--remove", source, target,
                          on_success=on_success_mirror)
        report.notify("Done")

        report.set_status("VerifyTargetBucket")

        target_bucket_objects, target_bucket_size = self._du_bucket(report, target)
        if source_bucket_objects != target_bucket_objects or source_bucket_size != target_bucket_size:
            msg = f"Mirror {source} to {target} failed: expected {source_bucket_objects} / {source_bucket_size} " \
                  f"actual {target_bucket_objects} / {target_bucket_size}"
            report.fatal(msg)
            raise RuntimeError(msg)

        report.set_status("exit function")

    def _du_bucket(self, report: Report, bucket: str):

        bucket_size = 0
        bucket_objects = 0

        def on_success_du(json: Any):
            report.debug(f"json={json}")
            nonlocal bucket_size
            bucket_size = json['size']
            nonlocal bucket_objects
            bucket_objects = json['objects']

        self._run_command(report, "du", "--versions", bucket, on_success=on_success_du)
        return bucket_objects, bucket_size

    def _mc_alias(self, alias: str, instance: S3Instance):
        report = self._report.get_sub_report(f"_mc_alias_{alias}", init_status="in function")
        self._run_command(report, "alias", "set", alias, instance.url(), instance.access_key(), instance.secret_key())
        report.set_status("exit function")

    def _run_command(self, report: Report, *args, on_error=default_on_error, on_success=default_on_success):
        report = report.get_sub_report("_run_command", init_status="in function")
        report.debug(f"args={args}")
        with subprocess.Popen([self._path_mc, '--json', '--config-dir', self._path_mc_config, *args],
                              stdout=subprocess.PIPE) as popen:
            for line in popen.stdout:
                # report.debug(f"line={line}")
                line_json = json.loads(line)
                status = line_json['status']
                if status == 'error':
                    error_type = line_json['error']['type']
                    if error_type == 'fatal':
                        report.fatal(f"{line}")
                        raise RuntimeError(f"failure when running mc command : {line_json['error']}")
                    else:
                        report.debug(f"error : {line}")
                        on_error(line_json)
                elif status == 'success':
                    on_success(line_json)
                else:
                    raise RuntimeError(f"Unknown status in mc output : {line}")

        report.set_status("exit function")
