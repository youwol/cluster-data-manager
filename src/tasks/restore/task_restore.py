"""Main class for restoration task."""
from tasks.restore.task_restore_cassandra import TaskRestoreCassandra
from tasks.restore.task_restore_s3 import TaskRestoreS3


class TaskRestore:
    """Restoration Task.

    Will call the subtasks.
    """
    def __init__(self,
                 task_restore_cassandra: TaskRestoreCassandra,
                 task_restore_s3: TaskRestoreS3):
        self._task_restore_cassandra = task_restore_cassandra
        self._task_restore_s3 = task_restore_s3

    def run(self):
        """Run the task."""
        self._task_restore_cassandra.run()
        self._task_restore_s3.run()
