"""Module for the restoration task & sub tasks.

Only export a getter for an instance of TaskRestore
"""
from .builder import build as build_task_restore

__all__ = ["build_task_restore"]
