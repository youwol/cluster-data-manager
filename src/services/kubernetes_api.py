from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Optional

from services.reporting import Report


class KubernetesApi:
    def __init__(self, report: Report):
        config.load_config()
        self._report = report.get_sub_report("k8s_api", init_status="ComponentInitialized")

    def get_ingress_class_name(self, ingress_name: str, ingress_namespace: str) -> Optional[str]:
        report = self._report.get_sub_report(f"get_ingress_class_name[{ingress_name}.{ingress_namespace}]",
                                             init_status="in function")
        api_networking = client.NetworkingV1Api()
        try:
            api_response = api_networking.read_namespaced_ingress(ingress_name, ingress_namespace)
        except ApiException as e:
            print("Exception when calling NetworkingV1Api->patch_namespaced_ingress: %s\n" % e)
            raise e
        result = api_response.spec.ingress_class_name
        report.debug(f"Result: {result}")
        return result

    def set_ingress_class_name(self, ingress_name: str, ingress_namespace: str,
                               ingress_class_name: Optional[str]):
        report = self._report.get_sub_report(
            f"set_ingress_class_name[{ingress_name}.{ingress_namespace}]({ingress_class_name})",
            init_status="in function")
        api_networking = client.NetworkingV1Api()
        patch = {"spec": {"ingressClassName": ingress_class_name}}
        try:
            api_response = api_networking.patch_namespaced_ingress(ingress_name, ingress_namespace, patch)
        except ApiException as e:
            print("Exception when calling NetworkingV1Api->patch_namespaced_ingress: %s\n" % e)
            raise e
        report.debug("Done")

    def get_config_map_value(self, config_map_name: str, config_map_namespace: str, key: str):
        report = self._report.get_sub_report(f"set_config_map_value[{config_map_name}.{config_map_namespace}#{key}]",
                                             init_status="in function")
        api_core = client.CoreV1Api()
        try:
            api_response = api_core.read_namespaced_config_map(config_map_name, config_map_namespace)
        except ApiException as e:
            print("Exception when calling CoreV1Api->patch_namespaced_config_map: %s\n" % e)
            raise e
        result = api_response.data[key]
        report.debug(f"Result: {result}")
        return result

    def set_config_map_value(self, config_map_name: str, config_map_namespace: str, key: str, value: str):
        report = self._report.get_sub_report(f"set_config_map_value[{config_map_name}.{config_map_namespace}#{key}]",
                                             init_status="in function")
        report.debug(f"value={value}")
        api_core = client.CoreV1Api()
        patch = {"data": {key: value}}
        try:
            api_response = api_core.patch_namespaced_config_map(config_map_name, config_map_namespace, patch)
        except ApiException as e:
            print("Exception when calling CoreV1Api->patch_namespaced_config_map: %s\n" % e)
            raise e
        report.debug("Done")
