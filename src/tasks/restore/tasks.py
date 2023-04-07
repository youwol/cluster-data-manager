from services import env, get_report_builder, get_cqlsh_commands_builder, get_mc_commands_builder


def get_task_restore_cassandra_builder():
    report_builder = get_report_builder()
    cqlsh_commands_builder = get_cqlsh_commands_builder()

    path_work_dir = env.existing_path(env.path_work_dir)
    keyspaces = env.strings_list(env.cql_keyspaces)
    tables = env.strings_list(env.cql_tables)
    overwrite = env.boolean(env.restore_overwrite, False)

    def builder():
        from . import tasks_context

        if tasks_context.restore_cassandra is None:
            from .task_restore_cassandra import TaskRestoreCassandra

            tasks_context.restore_cassandra = TaskRestoreCassandra(
                report=report_builder(),
                path_work_dir=path_work_dir,
                cqlsh_commands=cqlsh_commands_builder(),
                keyspaces=keyspaces,
                tables=tables,
                overwrite=overwrite
            )

        return tasks_context.restore_cassandra

    return builder


def get_task_restore_s3_builder():
    report_builder = get_report_builder()
    mc_commands_builder = get_mc_commands_builder()

    path_work_dir = env.existing_path(env.path_work_dir)
    s3_buckets = env.strings_list(env.s3_buckets)
    overwrite = env.boolean(env.restore_overwrite, False)

    def builder():
        from . import tasks_context

        if tasks_context.restore_s3 is None:
            from .task_restore_s3 import TaskRestoreS3

            tasks_context.restore_s3 = TaskRestoreS3(
                report=report_builder(),
                path_work_dir=path_work_dir,
                mc_commands=mc_commands_builder(),
                buckets=s3_buckets,
                overwrite=overwrite
            )

        return tasks_context.restore_s3

    return builder


def get_task_restore_builder():
    task_restore_cassandre_builder = get_task_restore_cassandra_builder()
    task_restore_s3_builder = get_task_restore_s3_builder()

    def builder():
        from . import tasks_context

        if tasks_context.restore is None:
            from .task_restore import TaskRestore

            tasks_context.restore = TaskRestore(
                task_restore_s3=task_restore_s3_builder(),
                task_restore_cassandra=task_restore_cassandre_builder()
            )

        return tasks_context.restore

    return builder
