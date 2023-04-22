"""Module for the Setup tasks.

Only export getters for instances of TaskSetup, configured either for setup_backup or setup_restore
"""
# relative
from .builder import backup as build_task_setup_backup
from .builder import restore as build_task_setup_restore

__all__ = ["build_task_setup_backup", "build_task_setup_restore"]
