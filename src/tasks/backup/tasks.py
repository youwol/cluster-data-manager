"""Manage backup (sub) tasks instances.

Use get_backup_task() to obtain a configured instance of TaskBackup.
Use get_<task>_builder() to obtain a nullary builder for a subtask.
"""
import datetime
from typing import Callable, Optional

from configuration import EnvVars, env_utils
from services import get_archiver_builder, get_cluster_maintenance_builder, get_cqlsh_commands_builder, \
    get_google_drive_builder, get_mc_commands_builder, get_report_builder
from services.keycloak_admin import KeycloakAdmin, KeycloakAdminCredentials
from tasks.backup.task_backup import TaskBackup
from tasks.backup.task_backup_cassandra import TaskBackupCassandra
from tasks.backup.task_backup_keycloak import TaskBackupKeycloak
from tasks.backup.task_backup_s3 import TaskBackupS3


class Context:
    """Hold subtasks instances."""
    s3: Optional[TaskBackupS3] = None
    cassandra: Optional[TaskBackupCassandra] = None
    keycloak: Optional[TaskBackupKeycloak] = None
    task: Optional[TaskBackup] = None


context = Context()


def get_task_backup_s3_builder() -> Callable[[], TaskBackupS3]:
    """Get a builder for a configured instance of the subtask backup_s3.

    Returns:
        Callable[[], TaskBackupS3]: a nullary builder for TaskBackupS3
    """
    if context.s3 is not None:
        return lambda: context.s3

    report_builder = get_report_builder()
    mc_commands_builder = get_mc_commands_builder()
    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)
    buckets = env_utils.strings_list(EnvVars.S3_BUCKETS)

    def builder() -> TaskBackupS3:

        if context.s3 is None:
            context.s3 = TaskBackupS3(report=report_builder(), path_work_dir=path_work_dir,
                                      mc_commands=mc_commands_builder(), buckets=buckets)
        return context.s3

    return builder


def get_task_backup_cassandra_builder() -> Callable[[], TaskBackupCassandra]:
    """Get a builder for a configured instance of the subtask backup_cassandra.

    Returns:
        Callable[[], TaskBackupCassandra]: a nullary builder for TaskBackupCassandra
    """
    if context.cassandra is not None:
        return lambda: context.cassandra

    report_builder = get_report_builder()
    cqlsh_commands_builder = get_cqlsh_commands_builder()
    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)
    keyspaces = env_utils.strings_list(EnvVars.CQL_KEYSPACES)
    tables = env_utils.strings_list(EnvVars.CQL_TABLES)

    def builder() -> TaskBackupCassandra:
        if context.cassandra is None:
            context.cassandra = TaskBackupCassandra(report=report_builder(), path_work_dir=path_work_dir,
                                                    cqlsh_commands=cqlsh_commands_builder(), tables=tables,
                                                    keyspaces=keyspaces)

        return context.cassandra

    return builder


def get_task_backup_keycloak_builder() -> Callable[[], TaskBackupKeycloak]:
    """Get a builder for a configured instance of the subtask backup_keycloak

    Returns:
        Callable[[], TaskBackupKeycloak]: a nullary builder for TaskBackupKeycloak
    """
    if context.keycloak is not None:
        return lambda: context.keycloak

    report_builder = get_report_builder()
    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)
    path_keycloak_status_file = env_utils.existing_path(EnvVars.PATH_KEYCLOAK_STATUS_FILE)
    keycloak_username = env_utils.not_empty_string(EnvVars.KEYCLOAK_USERNAME)
    keycloak_password = env_utils.not_empty_string(EnvVars.KEYCLOAK_PASSWORD)
    keycloak_base_url = env_utils.not_empty_string(EnvVars.KEYCLOAK_BASE_URL)

    def keycloak_admin_builder():
        return KeycloakAdmin(
            report=report_builder(),
            credentials=KeycloakAdminCredentials(
                realm="master",
                username=keycloak_username,
                password=keycloak_password
            ),
            base_url=keycloak_base_url
        )

    def builder() -> TaskBackupKeycloak:
        if context.keycloak is None:
            context.keycloak = TaskBackupKeycloak(
                report=report_builder(),
                path_work_dir=path_work_dir,
                keycloak_admin=keycloak_admin_builder(),
                path_keycloak_status_file=path_keycloak_status_file
            )

        return context.keycloak

    return builder


def get_task_backup() -> TaskBackup:
    """Get a configured instance of TaskBackup.

    Returns:
        TaskBackup: a configured instance of TaskBackup
    """
    if context.task is not None:
        return context.task

    report_builder = get_report_builder()
    task_backup_s3_builder = get_task_backup_s3_builder()
    task_backup_cassandra_builder = get_task_backup_cassandra_builder()
    task_backup_keycloak_builder = get_task_backup_keycloak_builder()
    archiver_builder = get_archiver_builder()
    google_drive_builder = get_google_drive_builder()
    cluster_maintenance_builder = get_cluster_maintenance_builder()

    path_log_file = env_utils.not_empty_string(EnvVars.PATH_WORK_DIR)
    job_uuid = env_utils.not_empty_string(EnvVars.JOB_UUID)
    type_backup = env_utils.not_empty_string(EnvVars.TYPE_BACKUP)
    google_drive_upload_file_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{job_uuid}.tgz"
    google_drive_upload_folder = type_backup

    context.task = TaskBackup(task_backup_s3=task_backup_s3_builder(),
                              task_backup_cassandra=task_backup_cassandra_builder(),
                              task_backup_keycloak=task_backup_keycloak_builder(),
                              google_drive=google_drive_builder(),
                              archive=archiver_builder().new_archive(),
                              google_drive_upload_file_name=google_drive_upload_file_name,
                              google_drive_upload_folder=google_drive_upload_folder,
                              cluster_maintenance=cluster_maintenance_builder(),
                              path_log_file=path_log_file)

    return context.task
