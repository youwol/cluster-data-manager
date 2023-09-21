"""Main class for restoration task."""
# standard library
from abc import ABC, abstractmethod

# typing
from typing import List

# application services
from youwol.data_manager.services.cluster_maintenance import ContextMaintenance
from youwol.data_manager.services.containers_readiness import ContainersReadiness


class RestoreSubtask(ABC):
    @abstractmethod
    def run(self):
        """Run the subtask"""


class Task:
    """Restoration Task.

    Will call the subtasks.
    """

    def __init__(
        self,
        containers_readiness: ContainersReadiness,
        subtasks: List[RestoreSubtask],
        context_maintenance: ContextMaintenance,
    ):
        """Simple constructor.

        Args:
            containers_readiness (ContainersReadiness): the containers readiness service
            subtasks (RestoreSubtask): list of subtasks to run
        """
        self._containers_readiness = containers_readiness
        self._context_maintenance = context_maintenance
        self._subtasks = subtasks

    def run(self) -> None:
        """Run the task."""
        self._containers_readiness.wait()

        with self._context_maintenance:
            for subtask in self._subtasks:
                subtask.run()
