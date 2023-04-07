from services import get_report_builder, env, get_archiver_builder, get_google_drive_builder


def get_task_setup_backup_builder():
    report_builder = get_report_builder()
    archiver_builder = get_archiver_builder()
    google_drive_builder = get_google_drive_builder()

    path_work_dir = env.existing_path(env.path_work_dir)

    def builder():
        from . import tasks_context

        if tasks_context.setup_backup is None:
            from .task_setup import TaskSetup

            tasks_context.setup_backup = TaskSetup(
                report=report_builder(),
                path_work_dir=path_work_dir,
                archiver=archiver_builder(),
                google_drive=google_drive_builder(),
                extract_items=["minio"]
            )

        return tasks_context.setup_backup

    return builder


def get_task_setup_restore_builder():
    report_builder = get_report_builder()
    archiver_builder = get_archiver_builder()
    google_drive_builder = get_google_drive_builder()

    path_work_dir = env.existing_path(env.path_work_dir)
    archive_name = env.not_empty_string(env.archive_name)

    def builder():
        from . import tasks_context

        if tasks_context.setup_restore is None:
            from .task_setup import TaskSetup

            tasks_context.setup_restore = TaskSetup(
                report=report_builder(),
                path_work_dir=path_work_dir,
                archiver=archiver_builder(),
                google_drive=google_drive_builder(),
                extract_items=["minio", "cql"],
                archive_name=archive_name
            )

        return tasks_context.setup_restore

    return builder
