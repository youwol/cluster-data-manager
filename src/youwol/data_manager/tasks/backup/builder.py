"""Manage backup (sub) tasks instances.

Use get_backup_task() to obtain a configured instance of TaskBackup.
Use get_<task>_builder() to obtain a nullary builder for a subtask.
"""
# standard library
import datetime

# typing
from typing import Callable, Optional

# application configuration
from youwol.data_manager.configuration import (
    Deployment,
    Installation,
    JobParams,
    env_utils,
)

# application services
from youwol.data_manager.services import (
    get_service_archiver_builder,
    get_service_cluster_maintenance_builder,
    get_service_cqlsh_commands_builder,
    get_service_google_drive_builder,
    get_service_mc_commands_builder,
    get_service_report_builder,
)
from youwol.data_manager.services.builder import (
    get_containers_readiness_kc_and_minio_builder,
)
from youwol.data_manager.services.keycloak_admin import (
    KeycloakAdmin,
    KeycloakAdminCredentials,
)

# relative
from .cassandra import Cassandra
from .keycloak import Keycloak
from .s3 import S3
from .task import Task


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
    path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
    buckets = env_utils.strings_list(JobParams.S3_BUCKETS)

    def builder() -> S3:
        if context.s3 is None:
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
    path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
    keyspaces = env_utils.strings_list(JobParams.CQL_KEYSPACES)
    tables = env_utils.strings_list(JobParams.CQL_TABLES)

    def builder() -> Cassandra:
        if context.cassandra is None:
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
    path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
    path_keycloak_status_file = env_utils.existing_path(
        Installation.PATH_KEYCLOAK_STATUS_FILE
    )
    keycloak_username = env_utils.not_empty_string(Deployment.KEYCLOAK_USERNAME)
    keycloak_password = env_utils.not_empty_string(Deployment.KEYCLOAK_PASSWORD)
    keycloak_base_url = env_utils.not_empty_string(Deployment.KEYCLOAK_BASE_URL)

    def keycloak_admin_builder() -> KeycloakAdmin:
        return KeycloakAdmin(
            report=report_builder(),
            credentials=KeycloakAdminCredentials(
                realm="master", username=keycloak_username, password=keycloak_password
            ),
            base_url=keycloak_base_url,
        )

    def builder() -> Keycloak:
        if context.keycloak is None:
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

    report_builder = get_service_report_builder()
    containers_readiness_builder = get_containers_readiness_kc_and_minio_builder()
    s3_builder = get_s3_builder()
    cassandra_builder = get_cassandra_builder()
    keycloak_builder = get_keycloak_builder()
    archiver_builder = get_service_archiver_builder()
    google_drive_builder = get_service_google_drive_builder()
    cluster_maintenance_builder = get_service_cluster_maintenance_builder()

    path_log_file = env_utils.existing_path(Installation.PATH_LOG_FILE)
    job_uuid = env_utils.not_empty_string(JobParams.JOB_UUID)
    type_backup = env_utils.not_empty_string(JobParams.TYPE_BACKUP)
    google_drive_upload_file_name = (
        f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{job_uuid}.tgz"
    )
    google_drive_upload_folder = type_backup

    context.task = Task(
        containers_readiness=containers_readiness_builder(),
        task_backup_s3=s3_builder(),
        task_backup_cassandra=cassandra_builder(),
        task_backup_keycloak=keycloak_builder(),
        google_drive=google_drive_builder(),
        archive=archiver_builder().new_archive(job_uuid=job_uuid),
        google_drive_upload_file_name=google_drive_upload_file_name,
        google_drive_upload_folder=google_drive_upload_folder,
        cluster_maintenance=cluster_maintenance_builder(),
        path_log_file=path_log_file,
    )

    return context.task
