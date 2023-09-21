"""Manage setup tasks instances.

Use get_<task>() to obtain a configured instance of TaskSetup for a given task.
"""
# typing
from typing import List, Optional

# application configuration
from youwol.data_manager.configuration import (
    ArchiveItem,
    Installation,
    JobParams,
    JobSubtasks,
    env_utils,
)

# application services
from youwol.data_manager.services import (
    get_service_archiver_builder,
    get_service_google_drive_builder,
    get_service_report_builder,
)

# relative
from .task import KeycloakDetails, Task


class Context:
    """Hold tasks instances."""

    task: Optional[Task] = None


context = Context()


def build() -> Task:
    """Build an instance of TaskSetup configured for setup_backup.

    Configured with:
      * no archive name (will download latest).
      * only extract Minio.

    Returns:
        TaskSetup: a instance of TaskSetup configured for setup_backup.
    """

    if context.task is not None:
        return context.task

    report_builder = get_service_report_builder()
    archiver_builder = get_service_archiver_builder()
    google_drive_builder = get_service_google_drive_builder()

    path_work_dir = env_utils.existing_path(Installation.PATH_WORK_DIR)
    archive_name = env_utils.maybe_string(JobParams.RESTORE_ARCHIVE_NAME)

    jobs_subtasks = env_utils.maybe_strings_list(
        JobParams.JOB_SUBTASKS, default=[JobSubtasks.ALL.value]
    )
    extract_items: List[ArchiveItem] = []
    if JobSubtasks.ALL.value in jobs_subtasks or JobSubtasks.S3.value in jobs_subtasks:
        extract_items.append(ArchiveItem.MINIO)
    if (
        JobSubtasks.ALL.value in jobs_subtasks
        or JobSubtasks.CASSANDRA.value in jobs_subtasks
    ):
        extract_items.append(ArchiveItem.CQL)
    if (
        JobSubtasks.ALL.value in jobs_subtasks
        or JobSubtasks.KEYCLOAK.value in jobs_subtasks
    ):
        extract_items.append(ArchiveItem.KEYCLOAK)

    keycloak_setup_details = KeycloakDetails(
        path_keycloak_status_file=env_utils.creating_file(
            Installation.PATH_KEYCLOAK_STATUS_FILE
        ),
        path_keycloak_script=env_utils.creating_file(Installation.PATH_KEYCLOAK_SCRIPT),
    )

    context.task = Task(
        report=report_builder(),
        path_work_dir=path_work_dir,
        keycloak_setup_details=keycloak_setup_details,
        archiver=archiver_builder(),
        google_drive=google_drive_builder(),
        extract_items=extract_items,
        archive_name=archive_name,
    )

    return context.task
