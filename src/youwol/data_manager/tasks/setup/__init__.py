"""Module for the Setup tasks.

Only export getters for instances of TaskSetup, configured either for setup_backup or setup_restore
"""
# relative
from .builder import build as build_task_setup

__all__ = ["build_task_setup"]
