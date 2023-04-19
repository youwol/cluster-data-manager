"""Main class (a context manager) and ancillary classes for cluster maintenance service.

Cluster maintenance service handle the set up and tear down of an Ingress redirecting cluster traffic for backends
to a custom maintenance page.
"""
import time
from contextlib import AbstractContextManager

from services.kubernetes_api import KubernetesApi, KubernetesConfigMapValueRef, KubernetesIngressRef
from services.reporting import Report


class MaintenanceDetails:
    """ Represent the k8s object references (Ingress className & ConfigMap data entry)
    necessary to handle maintenance mode."""
    def __init__(
            self,
            ingress_ref: KubernetesIngressRef,
            ingress_class_name, config_map_value_ref:
            KubernetesConfigMapValueRef,
            config_map_value
    ):
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

    def config_map_value_ref(self):
        """Simple getter.

        Returns:
            ConfigMapValueRef: the reference for the k8s ConfigMap data entry.
        """
        return self._config_map_value_ref

    def config_map_value(self):
        """Simple getter.

        Returns:
            str: the value of the k8s ConfigMap data entry for maintenance.
        """
        return self._config_map_value


class ClusterMaintenance(AbstractContextManager):
    """Context manager for maintenance mode.

    When entering the context, the maintenance mode is set up.
    When exiting the context, the maintenance mode is tear down.

    Note:
         Using a context manager ensure that the maintenance mode is tear down in almost all situations.
    """
    def __init__(self, report: Report, k8s_api: KubernetesApi, maintenance_details: MaintenanceDetails):
        self._report = report.get_sub_report("ClusterMaintenance", init_status="ComponentInitialized",
                                             default_status_level="NOTIFY")
        self._k8s_api = k8s_api
        self._details = maintenance_details
        self._original_config_map_value = None
        self._original_ingress_class_name = None

    def __enter__(self):
        self._report.set_status("MaintenanceModeON")
        self._original_config_map_value = self._k8s_api.get_config_map_value(self._details.config_map_value_ref())
        self._original_ingress_class_name = self._k8s_api.get_ingress_class_name(self._details.ingress_ref())
        self._k8s_api.set_config_map_value(self._details.config_map_value_ref(), self._details.config_map_value())
        self._k8s_api.set_ingress_class_name(self._details.ingress_ref(), self._details.ingress_class_name())
        time.sleep(5)

    def __exit__(self, *_):
        self._report.set_status("MaintenanceModeOFF")
        self._k8s_api.set_config_map_value(self._details.config_map_value_ref(), self._original_config_map_value)
        self._k8s_api.set_ingress_class_name(self._details.ingress_ref(), self._original_ingress_class_name)
