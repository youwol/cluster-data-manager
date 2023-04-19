"""Manage backup (sub) tasks instances.

Use get_backup_task() to obtain a configured instance of TaskBackup.
Use get_<task>_builder() to obtain a nullary builder for a subtask.
"""
import datetime
from typing import Callable, Optional

from services import env, get_archiver_builder, get_cluster_maintenance_builder, get_cqlsh_commands_builder, \
    get_google_drive_builder, get_mc_commands_builder, get_report_builder
from tasks.backup.task_backup import TaskBackup
from tasks.backup.task_backup_cassandra import TaskBackupCassandra
from tasks.backup.task_backup_s3 import TaskBackupS3


class Context:
    """Hold subtasks instances."""
    s3: Optional[TaskBackupS3] = None
    cassandra: Optional[TaskBackupCassandra] = None
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
    path_work_dir = env.existing_path(env.path_work_dir)
    buckets = env.strings_list(env.s3_buckets)

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
    path_work_dir = env.existing_path(env.path_work_dir)
    keyspaces = env.strings_list(env.cql_keyspaces)
    tables = env.strings_list(env.cql_tables)

    def builder() -> TaskBackupCassandra:
        if context.cassandra is None:
            context.cassandra = TaskBackupCassandra(report=report_builder(), path_work_dir=path_work_dir,
                                                    cqlsh_commands=cqlsh_commands_builder(), tables=tables,
                                                    keyspaces=keyspaces)

        return context.cassandra

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
    archiver_builder = get_archiver_builder()
    google_drive_builder = get_google_drive_builder()
    cluster_maintenance_builder = get_cluster_maintenance_builder()

    path_log_file = env.not_empty_string(env.path_log_file)
    job_uuid = env.not_empty_string(env.job_uuid)
    type_backup = env.not_empty_string(env.type_backup)
    google_drive_upload_file_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{job_uuid}.tgz"
    google_drive_upload_folder = type_backup

    context.task = TaskBackup(task_backup_s3=task_backup_s3_builder(),
                              task_backup_cassandra=task_backup_cassandra_builder(),
                              google_drive=google_drive_builder(),
                              archive=archiver_builder().new_archive(),
                              google_drive_upload_file_name=google_drive_upload_file_name,
                              google_drive_upload_folder=google_drive_upload_folder,
                              cluster_maintenance=cluster_maintenance_builder(),
                              path_log_file=path_log_file)

    return context.task
