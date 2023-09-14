"""Manage restoration task & subtasks instances.

Use get_<task>_builder to obtain an nullary builder for a subtask.
Use get_restore_task() to obtain a configured instance for TaskRestore.
"""
# typing
from typing import Callable, Optional

# application configuration
from youwol.data_manager.configuration import Installation, JobParams, env_utils

# application services
from youwol.data_manager.services import (
    get_service_cqlsh_commands_builder,
    get_service_mc_commands_builder,
    get_service_report_builder,
)
from youwol.data_manager.services.builder import get_containers_readiness_minio_builder

# relative
from .cassandra import Cassandra
from .s3 import S3
from .task import Task


class Context:
    """Hold subtasks instances."""

    s3: Optional[S3] = None
    cassandra: Optional[Cassandra] = None
    task: Optional[Task] = None


context = Context()


def get_s3_builder() -> Callable[[], S3]:
    """Get a builder for a configured instance of TaskRestoreS3.

    Returns:
        Callable[[], TaskRestoreS3]: a nullary builder for a configured instance of TaskRestoreS3
    """
    if context.s3 is not None:
        s3 = context.s3
        return lambda: s3

    report_builder = get_service_report_builder()
    mc_commands_builder = get_service_mc_commands_builder()

    path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
    s3_buckets = env_utils.strings_list(JobParams.S3_BUCKETS)
    overwrite = env_utils.boolean(JobParams.RESTORE_OVERWRITE, False)

    def builder() -> S3:
        if context.s3 is None:
            context.s3 = S3(
                report=report_builder(),
                path_work_dir=path_work_dir,
                mc_commands=mc_commands_builder(),
                buckets=s3_buckets,
                overwrite=overwrite,
            )

        return context.s3

    return builder


def get_cassandra_builder() -> Callable[[], Cassandra]:
    """Get a builder for a configured instance of TaskRestoreCassandra.

    Returns:
        Callable[[], TaskRestoreCassandra]: a nullary builder for a configured instance of TaskRestoreCassandra
    """
    if context.cassandra is not None:
        cassandra = context.cassandra
        return lambda: cassandra

    report_builder = get_service_report_builder()
    cqlsh_commands_builder = get_service_cqlsh_commands_builder()

    path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
    keyspaces = env_utils.strings_list(JobParams.CQL_KEYSPACES)
    tables = env_utils.strings_list(JobParams.CQL_TABLES)
    overwrite = env_utils.boolean(JobParams.RESTORE_OVERWRITE, False)

    def builder() -> Cassandra:
        if context.cassandra is None:
            context.cassandra = Cassandra(
                report=report_builder(),
                path_work_dir=path_work_dir,
                cqlsh_commands=cqlsh_commands_builder(),
                keyspaces=keyspaces,
                tables=tables,
                overwrite=overwrite,
            )

        return context.cassandra

    return builder


def build() -> Task:
    """Get a configured instance of TaskRestore.

    Returns:
        TaskRestore: a configured instance of TaskRestore
    """
    if context.task is not None:
        return context.task

    task_restore_cassandre_builder = get_cassandra_builder()
    task_restore_s3_builder = get_s3_builder()
    containers_readiness_builder = get_containers_readiness_minio_builder()

    context.task = Task(
        containers_readiness=containers_readiness_builder(),
        task_restore_s3=task_restore_s3_builder(),
        task_restore_cassandra=task_restore_cassandre_builder(),
    )

    return context.task
