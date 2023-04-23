"""Entry point for the docker image.

It has a main function, and expect exactly one command line argument : the name of the task to run.
"""
# data-manager configuration
from configuration import env_utils

# data-manager tasks
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


def run() -> None:
    """Run a task.

    Will run the task passed as the first positional command line parameter.
    """
    task_name = env_utils.arg_task_name()

    if task_name not in tasks_builder:
        raise RuntimeError(f"Unknown task {task_name}")

    task = tasks_builder[task_name]()
    task.run()


if __name__ == "__main__":
    run()
