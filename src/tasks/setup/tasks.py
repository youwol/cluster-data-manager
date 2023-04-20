"""Manage setup tasks instances.

Use get_<task>() to obtain a configured instance of TaskSetup for a given task.
"""
from typing import Any

from configuration import EnvVars, env_utils
from services import get_archiver_builder, get_google_drive_builder, get_report_builder
from tasks.setup.task_setup import TaskSetup


class Context:
    """Hold tasks instances."""
    backup = None
    restore = None


context = Context()


def get_task_setup_backup() -> TaskSetup:
    """Build an instance of TaskSetup configured for setup_backup.

    Configured with:
      * no archive name (will download latest).
      * only extract Minio.

    Returns:
        TaskSetup: a instance of TaskSetup configured for setup_backup.
    """
    if context.backup is not None:
        return context.backup

    report_builder = get_report_builder()
    archiver_builder = get_archiver_builder()
    google_drive_builder = get_google_drive_builder()

    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)

    context.backup = TaskSetup(report=report_builder(), path_work_dir=path_work_dir,
                               archiver=archiver_builder(), google_drive=google_drive_builder(),
                               extract_items=["minio"])

    return context.backup


def get_task_setup_restore() -> Any:
    """Build an instance of TaskSetup configured for setup_restore.

    Configured with:
      * archive name from environment.
      * extract everythinng.
    Returns:
        TaskSetup: a instance of TaskSetup configured for setup_restore
    """
    if context.restore is not None:
        return context.restore

    report_builder = get_report_builder()
    archiver_builder = get_archiver_builder()
    google_drive_builder = get_google_drive_builder()

    path_work_dir = env_utils.existing_path(EnvVars.PATH_WORK_DIR)
    archive_name = env_utils.not_empty_string(EnvVars.ARCHIVE_NAME)

    context.restore = TaskSetup(report=report_builder(), path_work_dir=path_work_dir,
                                      archiver=archiver_builder(), google_drive=google_drive_builder(),
                                      extract_items=["minio", "cql"], archive_name=archive_name)

    return context.restore
