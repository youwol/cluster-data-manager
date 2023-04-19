"""Entry point for the docker image.

It has a main function, and expect exactly one command line argument : the name of the task to run.
"""

from services import env
from tasks import get_task_backup, get_task_restore, get_task_setup_backup, get_task_setup_restore

tasks_getter = {
    "setup_backup": get_task_setup_backup,
    "backup": get_task_backup,
    "setup_restore": get_task_setup_restore,
    "restore": get_task_restore,
}

if __name__ == '__main__':

    TASK_NAME = env.arg_task_name()

    if TASK_NAME not in tasks_getter:
        raise RuntimeError(f"Unknown task {TASK_NAME}")

    task = tasks_getter[TASK_NAME]()
    task.run()
