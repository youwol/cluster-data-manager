"""Entry point for the docker image.

It has a main function, and expect exactly one command line argument : the name of the task to run.
"""
from configuration import env_utils
from tasks import (
    build_task_backup,
    build_task_restore,
    build_task_setup_backup,
    build_task_setup_restore,
)

tasks_builder = {
    "setup_backup": build_task_setup_backup,
    "backup": build_task_backup,
    "setup_restore": build_task_setup_restore,
    "restore": build_task_restore,
}

if __name__ == "__main__":
    TASK_NAME = env_utils.arg_task_name()

    if TASK_NAME not in tasks_builder:
        raise RuntimeError(f"Unknown task {TASK_NAME}")

    task = tasks_builder[TASK_NAME]()
    task.run()
