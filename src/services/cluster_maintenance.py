"""Main class (a context manager) and ancillary classes for cluster maintenance service.

Cluster maintenance service handle the set up and tear down of an Ingress redirecting cluster traffic for backends
to a custom maintenance page.
"""
import time
from contextlib import AbstractContextManager
from typing import Any, Optional

from .kubernetes_api import (
    KubernetesApi,
    KubernetesConfigMapValueRef,
    KubernetesIngressRef,
)
from .reporting import Report


class MaintenanceDetails:
    """Represent the k8s objects references and maintenance values."""

    def __init__(
        self,
        ingress_ref: KubernetesIngressRef,
        ingress_class_name: str,
        config_map_value_ref: KubernetesConfigMapValueRef,
        config_map_value: str,
    ):
        """Simple constructor.

        Args:
            ingress_ref (KubernetesIngressRef): the reference of the Ingress
            ingress_class_name (str): the className of the Ingress for maintenance
            config_map_value_ref (KubernetesConfigMapValueRef): the reference of the ConfigMap data entry
            config_map_value: the value of the ConfigMap data entry for maintenance
        """
        self._ingress_ref = ingress_ref
        self._ingress_class_name = ingress_class_name
        self._config_map_value_ref = config_map_value_ref
        self._config_map_value = config_map_value

    def ingress_ref(self) -> KubernetesIngressRef:
        """Simple getter.

        Returns:
            KubernetesIngressRef: the reference for the k8s Ingress.
        """
        return self._ingress_ref

    def ingress_class_name(self) -> str:
        """Simple getter.

        Returns:
            str: the k8s Ingress className for maintenance.
        """
        return self._ingress_class_name

    def config_map_value_ref(self) -> KubernetesConfigMapValueRef:
        """Simple getter.

        Returns:
            ConfigMapValueRef: the reference for the k8s ConfigMap data entry.
        """
        return self._config_map_value_ref

    def config_map_value(self) -> str:
        """Simple getter.

        Returns:
            str: the value of the k8s ConfigMap data entry for maintenance.
        """
        return self._config_map_value


class ClusterMaintenance(AbstractContextManager[None]):
    """Context manager for maintenance mode.

    When entering the context, the maintenance mode is set up.
    When exiting the context, the maintenance mode is tear down.

    Note:
         Using a context manager ensure that the maintenance mode is tear down in almost all situations.
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
        self._report = report.get_sub_report(
            "ClusterMaintenance",
            init_status="ComponentInitialized",
            default_status_level="NOTIFY",
        )
        self._k8s_api = k8s_api
        self._details = maintenance_details
        self._original_config_map_value: Optional[str] = None
        self._original_ingress_class_name: Optional[str] = None

    def __enter__(self) -> None:
        """Enter maintenance context.

        Will set the kubernetes objects for maintenance mode.

        Notes:
            Context maintenance yield nothing.
        """
        self._report.set_status("MaintenanceModeON")
        self._original_config_map_value = self._k8s_api.get_config_map_value(
            self._details.config_map_value_ref()
        )
        self._original_ingress_class_name = self._k8s_api.get_ingress_class_name(
            self._details.ingress_ref()
        )
        self._k8s_api.set_config_map_value(
            self._details.config_map_value_ref(), self._details.config_map_value()
        )
        self._k8s_api.set_ingress_class_name(
            self._details.ingress_ref(), self._details.ingress_class_name()
        )
        time.sleep(5)

    def __exit__(self, exec_type: Any, exec_value: Any, traceback: Any) -> None:
        """Exit maintenance context.

        Will restore the kubernetes objects as before entering maintenance mode.
        """
        self._report.set_status("MaintenanceModeOFF")
        self._k8s_api.set_config_map_value(
            self._details.config_map_value_ref(), self._original_config_map_value
        )
        self._k8s_api.set_ingress_class_name(
            self._details.ingress_ref(), self._original_ingress_class_name
        )
