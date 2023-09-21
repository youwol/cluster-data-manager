"""Manage restoration task & subtasks instances.

Use get_<task>_builder to obtain an nullary builder for a subtask.
Use get_restore_task() to obtain a configured instance for TaskRestore.
"""
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
    get_service_containers_readiness_builder,
    get_service_cqlsh_commands_builder,
    get_service_mc_commands_builder,
    get_service_report_builder,
)

# relative
from .cassandra import Cassandra
from .s3 import S3
from .task import RestoreSubtask, Task


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

    def builder() -> S3:
        if context.s3 is None:
            context.s3 = S3(
                report=report_builder(),
                path_work_dir=path_work_dir,
                mc_commands=mc_commands_builder(),
                buckets=s3_buckets,
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

    def builder() -> Cassandra:
        if context.cassandra is None:
            context.cassandra = Cassandra(
                report=report_builder(),
                path_work_dir=path_work_dir,
                cqlsh_commands=cqlsh_commands_builder(),
                keyspaces=keyspaces,
                tables=tables,
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

    job_subtasks = env_utils.maybe_strings_list(JobParams.JOB_SUBTASKS, ["all"])
    if JobSubtasks.ALL.value in job_subtasks and len(job_subtasks) != 1:
        raise RuntimeError(
            f"Env {JobParams.JOB_SUBTASKS} contains both 'all' and other elements"
        )

    subtask_s3_builder = get_s3_builder()
    subtask_cassandre_builder = get_cassandra_builder()
    containers_readiness_builder = get_service_containers_readiness_builder()
    subtasks: List[RestoreSubtask] = []
    if JobSubtasks.ALL.value in job_subtasks or JobSubtasks.S3.value in job_subtasks:
        subtasks.append(subtask_s3_builder())
    if (
        JobSubtasks.ALL.value in job_subtasks
        or JobSubtasks.CASSANDRA.value in job_subtasks
    ):
        subtasks.append(subtask_cassandre_builder())

    context.task = Task(
        containers_readiness=containers_readiness_builder(), subtasks=subtasks
    )

    return context.task
