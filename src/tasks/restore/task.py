"""Main class for restoration task."""
from .cassandra import Cassandra
from .s3 import S3


class Task:
    """Restoration Task.

    Will call the subtasks.
    """

    def __init__(self, task_restore_cassandra: Cassandra, task_restore_s3: S3):
        """Simple constructor.

        Args:
            task_restore_cassandra (Cassandra): the cassandra restore task
            task_restore_s3 (S3):  the S3 restore task
        """
        self._task_restore_cassandra = task_restore_cassandra
        self._task_restore_s3 = task_restore_s3

    def run(self) -> None:
        """Run the task."""
        self._task_restore_cassandra.run()
        self._task_restore_s3.run()
