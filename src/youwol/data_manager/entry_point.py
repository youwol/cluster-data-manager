"""Entry point for the docker image.

It has a main function, and expect exactly one command line argument : the name of the task to run.
"""

# application configuration
from youwol.data_manager.configuration import env_utils

# application tasks
from youwol.data_manager.tasks import (
    build_task_backup,
    build_task_restore,
    build_task_setup,
)

tasks_builder = {
    "setup": build_task_setup,
    "backup": build_task_backup,
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
