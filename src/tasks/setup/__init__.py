"""Module for the Setup tasks.

Only export getters for instances of TaskSetup, configured either for setup_backup or setup_restore
"""
from .tasks import get_task_setup_backup, get_task_setup_restore
