"""Manage restoration task & subtasks instances.

Use get_<task>_builder to obtain an nullary builder for a subtask.
Use get_restore_task() to obtain a configured instance for TaskRestore.
"""
from typing import Callable, Optional

from configuration import EnvVars, env_utils
from services import get_cqlsh_commands_builder, get_mc_commands_builder, get_report_builder
from tasks.restore.task_restore import TaskRestore
from tasks.restore.task_restore_cassandra import TaskRestoreCassandra
from tasks.restore.task_restore_s3 import TaskRestoreS3


class Context:
    """Hold subtasks instances."""
    s3: Optional[TaskRestoreS3] = None
    cassandra: Optional[TaskRestoreCassandra] = None
    task: Optional[TaskRestore] = None


context = Context()


def get_task_restore_s3_builder() -> Callable[[], TaskRestoreS3]:
    """Get a builder for a configured instance of TaskRestoreS3.

    Returns:
        Callable[[], TaskRestoreS3]: a nullary builder for a configured instance of TaskRestoreS3
    """
    if context.s3 is not None:
        return lambda: context.s3

    report_builder = get_report_builder()
    mc_commands_builder = get_mc_commands_builder()

    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)
    s3_buckets = env_utils.strings_list(EnvVars.S3_BUCKETS)
    overwrite = env_utils.boolean(EnvVars.RESTORE_OVERWRITE, False)

    def builder() -> TaskRestoreS3:
        if context.s3 is None:
            context.s3 = TaskRestoreS3(report=report_builder(), path_work_dir=path_work_dir,
                                       mc_commands=mc_commands_builder(), buckets=s3_buckets, overwrite=overwrite)

        return context.s3

    return builder


def get_task_restore_cassandra_builder() -> Callable[[], TaskRestoreCassandra]:
    """ Get a builder for a configured instance of TaskRestoreCassandra.

    Returns:
        Callable[[], TaskRestoreCassandra]: a nullary builder for a configured instance of TaskRestoreCassandra
    """
    if context.cassandra is not None:
        return lambda: context.cassandra

    report_builder = get_report_builder()
    cqlsh_commands_builder = get_cqlsh_commands_builder()

    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)
    keyspaces = env_utils.strings_list(EnvVars.CQL_KEYSPACES)
    tables = env_utils.strings_list(EnvVars.CQL_TABLES)
    overwrite = env_utils.boolean(EnvVars.RESTORE_OVERWRITE, False)

    def builder() -> TaskRestoreCassandra:
        if context.cassandra is None:
            context.cassandra = TaskRestoreCassandra(report=report_builder(), path_work_dir=path_work_dir,
                                                     cqlsh_commands=cqlsh_commands_builder(), keyspaces=keyspaces,
                                                     tables=tables, overwrite=overwrite)

        return context.cassandra

    return builder


def get_task_restore() -> TaskRestore:
    """Get a configured instance of TaskRestore.

    Returns:
        TaskRestore: a configured instance of TaskRestore
    """
    if context.task is not None:
        return context.task

    task_restore_cassandre_builder = get_task_restore_cassandra_builder()
    task_restore_s3_builder = get_task_restore_s3_builder()

    context.task = TaskRestore(task_restore_s3=task_restore_s3_builder(),
                               task_restore_cassandra=task_restore_cassandre_builder())

    return context.task
