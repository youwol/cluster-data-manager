import time
from contextlib import AbstractContextManager

from services.kubernetes_api import KubernetesApi
from services.reporting import Report


class MaintenanceDetails:
    def __init__(self, ingress_name: str, ingress_namespace: str, config_map_name: str, config_map_namespace: str,
                 ingress_class_name: str, config_map_key: str, config_map_value: str):
        self._ingress_name = ingress_name
        self._ingress_namespace = ingress_namespace
        self._ingress_class_name = ingress_class_name
        self._config_map_name = config_map_name
        self._config_map_namespace = config_map_namespace
        self._config_map_key = config_map_key
        self._config_map_value = config_map_value

    def ingress_name(self):
        return self._ingress_name

    def ingress_namespace(self):
        return self._ingress_namespace

    def ingress_class_name(self):
        return self._ingress_class_name

    def config_map_name(self):
        return self._config_map_name

    def config_map_namespace(self):
        return self._config_map_namespace

    def config_map_key(self):
        return self._config_map_key

    def config_map_value(self):
        return self._config_map_value


class ClusterMaintenance(AbstractContextManager):
    def __init__(self, report: Report, k8s_api: KubernetesApi, maintenance_details: MaintenanceDetails):
        self._report = report.get_sub_report("ClusterMaintenance", init_status="ComponentInitialized",
                                             default_status_level="NOTIFY")
        self._k8s_api = k8s_api
        self._maintenance_details = maintenance_details

    def __enter__(self):
        self._report.set_status("MaintenanceModeON")
        self._original_config_map_value = self._k8s_api.get_config_map_value(
            self._maintenance_details.config_map_name(),
            self._maintenance_details.config_map_namespace(),
            self._maintenance_details.config_map_key())
        self._original_ingress_class_name = self._k8s_api.get_ingress_class_name(
            self._maintenance_details.ingress_name(),
            self._maintenance_details.ingress_namespace()
        )
        self._k8s_api.set_config_map_value(
            self._maintenance_details.config_map_name(),
            self._maintenance_details.config_map_namespace(),
            self._maintenance_details.config_map_key(),
            self._maintenance_details.config_map_value()
        )
        self._k8s_api.set_ingress_class_name(
            self._maintenance_details.ingress_name(),
            self._maintenance_details.ingress_namespace(),
            self._maintenance_details.ingress_class_name()
        )
        time.sleep(5)

    def __exit__(self, *_):
        self._report.set_status("MaintenanceModeOFF")
        self._k8s_api.set_config_map_value(
            self._maintenance_details.config_map_name(),
            self._maintenance_details.config_map_namespace(),
            self._maintenance_details.config_map_key(),
            self._original_config_map_value
        )
        self._k8s_api.set_ingress_class_name(
            self._maintenance_details.ingress_name(),
            self._maintenance_details.ingress_namespace(),
            self._original_ingress_class_name)
