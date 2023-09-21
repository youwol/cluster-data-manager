"""Main class (a context manager) and ancillary classes for cluster maintenance service.

Cluster maintenance service handle the set up and tear down of an Ingress redirecting cluster traffic for backends
to a custom maintenance page.
"""
# standard library
import abc
import time

from contextlib import AbstractContextManager
from dataclasses import dataclass

# typing
from typing import Any, Optional

# relative
from .kubernetes_api import (
    KubernetesApi,
    KubernetesConfigMapValueRef,
    KubernetesIngressRef,
)
from .reporting import Report


@dataclass(frozen=True, kw_only=True)
class MaintenanceDetails:
    """Represent the k8s objects references and maintenance values."""

    ingress_ref: KubernetesIngressRef
    ingress_class_name: str
    config_map_value_ref: KubernetesConfigMapValueRef
    config_map_value: str


class ContextMaintenance(AbstractContextManager[None]):
    """Context manager for maintenance mode.

    When entering the context, the maintenance mode is set up.
    When exiting the context, the maintenance mode is tear down.

    Note:
         Using a context manager ensure that the maintenance mode is tear down in almost all situations.
    """

    def __init__(self, report: Report, task_name: str):
        self._report = report.get_sub_report(
            task_name,
            init_status="ComponentInitialized",
            default_status_level="NOTIFY",
        )

    def __enter__(self) -> None:
        """Enter maintenance context.

        Notes:
            Context maintenance yield nothing.
        """
        self._report.set_status("MaintenanceModeOn")
        self._set_up_maintenance_mode()

    def __exit__(self, exec_type: Any, exec_value: Any, traceback: Any) -> None:
        """Exit maintenance context."""
        self._report.set_status("MaintenanceModeOFF")
        self._tear_down_maintenance_mode()

    @abc.abstractmethod
    def _set_up_maintenance_mode(self):
        """To be implemented by concrete classes"""

    @abc.abstractmethod
    def _tear_down_maintenance_mode(self):
        """To be implemented by concrete classes"""


class ClusterMaintenance(ContextMaintenance):
    """Manage maintenance mode into a K8S cluster.

    See infra/static-assets for details about K8S cluster maintenance mode
    """

    def __init__(
        self,
        report: Report,
        k8s_api: KubernetesApi,
        maintenance_details: MaintenanceDetails,
    ):
        """Simple constructor.

        Args:
            report (Report): the report
            k8s_api (KubernetesApi): the kubernetes API service
            maintenance_details (MaintenanceDetails): the maintenance details
        """
        super().__init__(report, "ClusterMaintenance")
        self._k8s_api = k8s_api
        self._details = maintenance_details
        self._original_config_map_value: Optional[str] = None
        self._original_ingress_class_name: Optional[str] = None

    def _set_up_maintenance_mode(self) -> None:
        """set up maintenance mode.

        Will set the kubernetes objects for maintenance mode.

        Notes:
            Context maintenance yield nothing.
        """
        self._original_config_map_value = self._k8s_api.get_config_map_value(
            self._details.config_map_value_ref
        )
        self._original_ingress_class_name = self._k8s_api.get_ingress_class_name(
            self._details.ingress_ref
        )
        self._k8s_api.set_config_map_value(
            self._details.config_map_value_ref, self._details.config_map_value
        )
        self._k8s_api.set_ingress_class_name(
            self._details.ingress_ref, self._details.ingress_class_name
        )
        time.sleep(5)

    def _tear_down_maintenance_mode(self) -> None:
        """tear down maintenance mode.

        Will restore the kubernetes objects as before entering maintenance mode.
        """
        self._k8s_api.set_config_map_value(
            self._details.config_map_value_ref, self._original_config_map_value
        )
        self._k8s_api.set_ingress_class_name(
            self._details.ingress_ref, self._original_ingress_class_name
        )


class NoopMaintenanceMode(ContextMaintenance):
    def __init__(self, report: Report):
        super().__init__(report, "NoopMaintenanceMode")

    def _set_up_maintenance_mode(self):
        self._report.notify(
            "Set up maintenance mode does not do anything since Noop Maintenance Mode"
        )

    def _tear_down_maintenance_mode(self):
        self._report.notify(
            "Tear down maintenance mode does not do anything since Noop Maintenance Mode"
        )
