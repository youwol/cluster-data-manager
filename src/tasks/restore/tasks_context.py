from typing import Optional

from .task_restore import TaskRestore
from .task_restore_cassandra import TaskRestoreCassandra
from .task_restore_s3 import TaskRestoreS3

restore_cassandra: Optional[TaskRestoreCassandra] = None
restore_s3: Optional[TaskRestoreS3] = None
restore: Optional[TaskRestore] = None
