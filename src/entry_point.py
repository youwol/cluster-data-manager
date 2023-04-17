import sys


def main(task: str):
    if task == "backup":
        get_task_backup().run()
    elif task == "setup_backup":
        get_task_setup_backup().run()
    elif task == "setup_restore":
        get_task_setup_restore().run()
    elif task == "restore":
        get_task_restore().run()
    else:
        raise RuntimeError(f"Unknown task {task}")


def get_task_backup():
    from tasks import get_task_backup_builder
    builder = get_task_backup_builder()
    return builder()


def get_task_restore():
    from tasks import get_task_restore_builder
    builder = get_task_restore_builder()
    return builder()


def get_task_setup_backup():
    from tasks import get_task_setup_backup_builder
    builder = get_task_setup_backup_builder()
    return builder()


def get_task_setup_restore():
    from tasks import get_task_setup_restore_builder
    builder = get_task_setup_restore_builder()
    return builder()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise RuntimeError("entry_point.py expect exactly one argument")
    arg = sys.argv[1]
    main(arg)
