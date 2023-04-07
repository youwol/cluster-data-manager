import datetime

from services import get_report_builder, env, get_mc_commands_builder, get_cqlsh_commands_builder, \
    get_google_drive_builder, get_archiver_builder, get_cluster_maintenance_builder


def get_task_backup_s3_builder():
    report_builder = get_report_builder()
    mc_commands_builder = get_mc_commands_builder()
    path_work_dir = env.existing_path(env.path_work_dir)
    buckets = env.strings_list(env.s3_buckets)

    def builder():
        from tasks.backup import tasks_context

        if tasks_context.s3 is None:
            from tasks.backup.task_backup_s3 import TaskBackupS3

            tasks_context.s3 = TaskBackupS3(report=report_builder(), path_work_dir=path_work_dir,
                                            mc_commands=mc_commands_builder(), buckets=buckets)
        return tasks_context.s3

    return builder


def get_task_backup_cassandra_builder():
    report_builder = get_report_builder()
    cqlsh_commands_builder = get_cqlsh_commands_builder()
    path_work_dir = env.existing_path(env.path_work_dir)
    keyspaces = env.strings_list(env.cql_keyspaces)
    tables = env.strings_list(env.cql_tables)

    def builder():
        from tasks.backup import tasks_context

        if tasks_context.cassandra is None:
            from tasks.backup.task_backup_cassandra import TaskBackupCassandra

            tasks_context.cassandra = TaskBackupCassandra(report=report_builder(),
                                                          path_work_dir=path_work_dir,
                                                          cqlsh_commands=cqlsh_commands_builder(),
                                                          tables=tables,
                                                          keyspaces=keyspaces)

        return tasks_context.cassandra

    return builder


def get_task_backup_builder():
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

    def builder():
        from tasks.backup import tasks_context

        if tasks_context.task_backup is None:
            from tasks.backup.task_backup import TaskBackup

            tasks_context.task_backup = TaskBackup(
                task_backup_s3=task_backup_s3_builder(),
                task_backup_cassandra=task_backup_cassandra_builder(),
                google_drive=google_drive_builder(),
                archive=archiver_builder().new_archive(),
                google_drive_upload_file_name=google_drive_upload_file_name,
                google_drive_upload_folder=google_drive_upload_folder,
                cluster_maintenance=cluster_maintenance_builder(),
                path_log_file=path_log_file
            )

        return tasks_context.task_backup

    return builder
