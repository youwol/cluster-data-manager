"""Manage backup (sub) tasks instances.

Use get_backup_task() to obtain a configured instance of TaskBackup.
Use get_<task>_builder() to obtain a nullary builder for a subtask.
"""

# standard library
import datetime

# typing
from typing import Callable, List, Optional

# application configuration
from youwol.data_manager.configuration import (
    Installation,
    JobParams,
    JobSubtasks,
    env_utils,
)

# application services
from youwol.data_manager.services import (
    get_service_archiver_builder,
    get_service_containers_readiness_builder,
    get_service_context_maintenance_builder,
    get_service_cqlsh_commands_builder,
    get_service_google_drive_builder,
    get_service_mc_commands_builder,
    get_service_report_builder,
)

# relative
from ..common.keycloak import get_keycloak_admin_builder
from .cassandra import Cassandra
from .keycloak import Keycloak
from .s3 import S3
from .task import BackupSubtask, Task


class Context:
    """Hold subtasks instances."""

    s3: Optional[S3] = None
    cassandra: Optional[Cassandra] = None
    keycloak: Optional[Keycloak] = None
    task: Optional[Task] = None


context = Context()


def get_s3_builder() -> Callable[[], S3]:
    """Get a builder for a configured instance of the subtask backup_s3.

    Returns:
        Callable[[], TaskBackupS3]: a nullary builder for TaskBackupS3
    """
    if context.s3 is not None:
        s3 = context.s3
        return lambda: s3

    report_builder = get_service_report_builder()
    mc_commands_builder = get_service_mc_commands_builder()

    def builder() -> S3:
        if context.s3 is None:
            path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
            buckets = env_utils.strings_list(JobParams.S3_BUCKETS)

            context.s3 = S3(
                report=report_builder(),
                path_work_dir=path_work_dir,
                mc_commands=mc_commands_builder(),
                buckets=buckets,
            )
        return context.s3

    return builder


def get_cassandra_builder() -> Callable[[], Cassandra]:
    """Get a builder for a configured instance of the subtask backup_cassandra.

    Returns:
        Callable[[], TaskBackupCassandra]: a nullary builder for TaskBackupCassandra
    """
    if context.cassandra is not None:
        cassandra = context.cassandra
        return lambda: cassandra

    report_builder = get_service_report_builder()
    cqlsh_commands_builder = get_service_cqlsh_commands_builder()

    def builder() -> Cassandra:
        if context.cassandra is None:
            path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
            keyspaces = env_utils.strings_list(JobParams.CQL_KEYSPACES)
            tables = env_utils.strings_list(JobParams.CQL_TABLES)

            context.cassandra = Cassandra(
                report=report_builder(),
                path_work_dir=path_work_dir,
                cqlsh_commands=cqlsh_commands_builder(),
                tables=tables,
                keyspaces=keyspaces,
            )

        return context.cassandra

    return builder


def get_keycloak_builder() -> Callable[[], Keycloak]:
    """Get a builder for a configured instance of the subtask backup_keycloak.

    Returns:
        Callable[[], TaskBackupKeycloak]: a nullary builder for TaskBackupKeycloak
    """
    if context.keycloak is not None:
        keycloak = context.keycloak
        return lambda: keycloak

    report_builder = get_service_report_builder()
    keycloak_admin_builder = get_keycloak_admin_builder()

    def builder() -> Keycloak:
        if context.keycloak is None:
            path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
            path_keycloak_status_file = env_utils.existing_path(
                Installation.PATH_KEYCLOAK_STATUS_FILE
            )

            context.keycloak = Keycloak(
                report=report_builder(),
                path_work_dir=path_work_dir,
                keycloak_admin=keycloak_admin_builder(),
                path_keycloak_status_file=path_keycloak_status_file,
            )

        return context.keycloak

    return builder


def build() -> Task:
    """Get a configured instance of TaskBackup.

    Returns:
        TaskBackup: a configured instance of TaskBackup
    """
    if context.task is not None:
        return context.task

    archiver_builder = get_service_archiver_builder()
    google_drive_builder = get_service_google_drive_builder()
    containers_readiness_builder = get_service_containers_readiness_builder()
    context_maintenance_builder = get_service_context_maintenance_builder()

    path_log_file = env_utils.existing_path(Installation.PATH_LOG_FILE)
    job_uuid = env_utils.not_empty_string(JobParams.JOB_UUID)
    type_backup = env_utils.not_empty_string(JobParams.TYPE_BACKUP)
    google_drive_upload_file_name = (
        f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{job_uuid}.tgz"
    )
    google_drive_upload_folder = type_backup

    job_subtasks = env_utils.maybe_strings_list(JobParams.JOB_SUBTASKS, ["all"])
    if JobSubtasks.ALL.value in job_subtasks and len(job_subtasks) != 1:
        raise RuntimeError(
            f"Env {JobParams.JOB_SUBTASKS} contains both 'all' and other elements"
        )

    subtask_s3_builder = get_s3_builder()
    subtask_cassandra_builder = get_cassandra_builder()
    subtask_keycloak_builder = get_keycloak_builder()
    subtasks: List[BackupSubtask] = []
    if JobSubtasks.ALL.value in job_subtasks or JobSubtasks.S3.value in job_subtasks:
        subtasks.append(subtask_s3_builder())
    if (
        JobSubtasks.ALL.value in job_subtasks
        or JobSubtasks.CASSANDRA.value in job_subtasks
    ):
        subtasks.append(subtask_cassandra_builder())
    if (
        JobSubtasks.ALL.value in job_subtasks
        or JobSubtasks.KEYCLOAK.value in job_subtasks
    ):
        subtasks.append(subtask_keycloak_builder())

    context.task = Task(
        containers_readiness=containers_readiness_builder(),
        subtasks=subtasks,
        google_drive=google_drive_builder(),
        archive=archiver_builder().new_archive(job_uuid=job_uuid),
        google_drive_upload_file_name=google_drive_upload_file_name,
        google_drive_upload_folder=google_drive_upload_folder,
        context_maintenance=context_maintenance_builder(),
        path_log_file=path_log_file,
    )

    return context.task
