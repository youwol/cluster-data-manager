"""Manage setup tasks instances.

Use get_<task>() to obtain a configured instance of TaskSetup for a given task.
"""
from typing import Any, Optional

from configuration import ConfigEnvVars, env_utils
from services import get_service_archiver_builder, get_service_google_drive_builder, get_service_report_builder
from .task import KeycloakDetails, Task


class Context:
    """Hold tasks instances."""
    backup: Optional[Task] = None
    restore: Optional[Task] = None


context = Context()


def backup() -> Task:
    """Build an instance of TaskSetup configured for setup_backup.

    Configured with:
      * no archive name (will download latest).
      * only extract Minio.

    Returns:
        TaskSetup: a instance of TaskSetup configured for setup_backup.
    """
    if context.backup is not None:
        return context.backup

    report_builder = get_service_report_builder()
    archiver_builder = get_service_archiver_builder()
    google_drive_builder = get_service_google_drive_builder()

    path_work_dir = env_utils.existing_path(ConfigEnvVars.PATH_WORK_DIR)

    keycloak_setup_details = KeycloakDetails(
        path_keycloak_status_file=env_utils.creating_file(ConfigEnvVars.PATH_KEYCLOAK_STATUS_FILE),
        path_keycloak_script=env_utils.creating_file(ConfigEnvVars.PATH_KEYCLOAK_SCRIPT)
    )

    context.backup = Task(
        report=report_builder(),
        path_work_dir=path_work_dir,
        keycloak_setup_details=keycloak_setup_details,
        archiver=archiver_builder(),
        google_drive=google_drive_builder(),
        extract_items=["minio"]
    )

    return context.backup


def restore() -> Any:
    """Build an instance of TaskSetup configured for setup_restore.

    Configured with:
      * archive name from environment.
      * extract everythinng.
    Returns:
        TaskSetup: a instance of TaskSetup configured for setup_restore
    """
    if context.restore is not None:
        return context.restore

    report_builder = get_service_report_builder()
    archiver_builder = get_service_archiver_builder()
    google_drive_builder = get_service_google_drive_builder()

    path_work_dir = env_utils.existing_path(ConfigEnvVars.PATH_WORK_DIR)
    archive_name = env_utils.not_empty_string(ConfigEnvVars.RESTORE_ARCHIVE_NAME)

    context.restore = Task(
        report=report_builder(),
        path_work_dir=path_work_dir,
        archiver=archiver_builder(),
        google_drive=google_drive_builder(),
        extract_items=["minio", "cql"],
        archive_name=archive_name
    )

    return context.restore
