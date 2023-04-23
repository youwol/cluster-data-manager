"""Main class and ancillary classes for service kubernetes_api.

Manipulate k8s Ingress className and ConfigMap data entry value.
"""
# standard library
from dataclasses import dataclass

# typing
from typing import Optional

# Kubernetes
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

# relative
from .reporting import Report


@dataclass(frozen=True, kw_only=True)
class KubernetesIngressRef:
    """Represent an Ingress reference."""

    name: str
    namespace: str

    def __repr__(self) -> str:
        """Stringify.

        Returns:
            str: <name>.<namespace>
        """
        return f"{self.name}.{self.namespace}"


@dataclass(frozen=True, kw_only=True)
class KubernetesConfigMapValueRef:
    """Represent an ConfigMap data value reference."""

    name: str
    namespace: str
    key: str

    def __repr__(self) -> str:
        """Stringify.

        Returns:
            str: <name>.<namespace>#<key>
        """
        return f"{self.name}.{self.namespace}#{self.key}"


class KubernetesApi:
    """Class implementing a service for manipulating k8s Ingress className and ConfigMap data entry value."""

    def __init__(
        self,
        report: Report,
        kube_config: Optional[str],
        kube_config_context: Optional[str],
    ):
        """Construct and confugre kubernetes API.

        If kube_config is not provided, will default to in cluster configuration (a service account token mounted by
        Kubernetes).
        If kube_config is provided, will use it.
        If kube_config_context is provided but no kube_config is provided, will ignore it verbosely.

        Args:
            report (Report): the report
            kube_config (Optional[str]): path to the kube_config file
            kube_config_context (Optional[str]): name of a context defined in the kube_config file
        """
        self._report = report.get_sub_report(
            "kubernetes_api", init_status="InitializingComponent"
        )
        if kube_config is None:
            if kube_config_context is not None:
                self._report.warning(
                    "ignoring kubernetes config context because"
                    " no kubernetes config file is configured"
                )
            self._report.notify("using Pod service account")
            config.incluster_config.load_incluster_config()
        else:
            if kube_config_context is None:
                ctx_msg = "without specific context"
            else:
                ctx_msg = f"with context '{kube_config_context}'"
            self._report.notify(
                f"using kubernetes config file '{kube_config}' {ctx_msg}"
            )
            config.kube_config.load_kube_config(
                config_file=kube_config,
                context=kube_config_context,
                persist_config=False,
            )
        self._report.notify("Done")

    def get_ingress_class_name(
        self, ingress_ref: KubernetesIngressRef
    ) -> Optional[str]:
        """Get an Ingress className, if such attribute is defined.

        Args:
            ingress_ref (KubernetesIngressRef): the Ingress reference.

        Returns:
            Optional[str]: the Ingress className, or None if no such attribute exists.
        """
        report = self._report.get_sub_report(
            f"get_ingress_class_name[{ingress_ref}]", init_status="in function"
        )
        api_networking = client.NetworkingV1Api()

        try:
            api_response = api_networking.read_namespaced_ingress(
                namespace=ingress_ref.namespace,
                name=ingress_ref.name,
            )
        except ApiException as error:
            msg = f"Exception when calling NetworkingV1Api->patch_namespaced_ingress: {error}"
            report.fatal(msg)
            raise RuntimeError(msg) from error

        spec_ingress = api_response.spec
        if spec_ingress is None:
            raise RuntimeError(f"Ingress '{ingress_ref}' has no spec")

        result = spec_ingress.ingress_class_name
        report.debug(f"Result: {result}")
        return result

    def set_ingress_class_name(
        self, ingress_ref: KubernetesIngressRef, ingress_class_name: Optional[str]
    ) -> None:
        """Set or remove an Ingress className.

        Args:
            ingress_ref (KubernetesIngressRef): the Ingress reference.
            ingress_class_name (Optional[str]): the className, or None to remove attribtue.

        """
        report = self._report.get_sub_report(
            f"set_ingress_class_name[{ingress_ref}]({ingress_class_name})",
            init_status="in function",
        )
        report.debug(f"value={ingress_class_name}")
        api_networking = client.NetworkingV1Api()

        try:
            _ = api_networking.patch_namespaced_ingress(
                namespace=ingress_ref.namespace,
                name=ingress_ref.name,
                body={"spec": {"ingressClassName": ingress_class_name}},
            )
        except ApiException as error:
            msg = f"Exception when calling NetworkingV1Api->patch_namespaced_ingress: {error}"
            report.fatal(msg)
            raise RuntimeError(msg) from error

        report.debug("Done")

    def get_config_map_value(
        self, config_map_value_ref: KubernetesConfigMapValueRef
    ) -> Optional[str]:
        """Get the value of a ConfigMap data entry.

        Args:
            config_map_value_ref (KubernetesConfigMapValueRef): the ConfigMap data entry reference.

        Returns:
            str: the value.
        """
        report = self._report.get_sub_report(
            f"set_config_map_value[{config_map_value_ref}]", init_status="in function"
        )
        api_core = client.CoreV1Api()

        try:
            api_response = api_core.read_namespaced_config_map(
                namespace=config_map_value_ref.namespace,
                name=config_map_value_ref.name,
            )
        except ApiException as error:
            msg = f"Exception when calling CoreV1Api->patch_namespaced_config_map: {error}"
            report.fatal(msg)
            raise RuntimeError(msg) from error

        config_map_data = api_response.data
        if config_map_data is None:
            raise RuntimeError(f"ConfigMap '{config_map_value_ref}' has no data")

        if config_map_value_ref.key not in config_map_data:
            raise RuntimeError(
                f"ConfigMap data entry '{config_map_value_ref}' does not exist"
            )

        result = config_map_data[config_map_value_ref.key]
        report.debug(f"Result: {result}")
        return result

    def set_config_map_value(
        self, config_map_value_ref: KubernetesConfigMapValueRef, value: Optional[str]
    ) -> None:
        """Set the value of a ConfigMap data entry.

        Args:
            config_map_value_ref (KubernetesConfigMapValueRef): the ConfigMap data entry reference.
            value (str): the value.
        """
        report = self._report.get_sub_report(
            f"set_config_map_value[{config_map_value_ref}]", init_status="in function"
        )
        report.debug(f"value={value}")
        api_core = client.CoreV1Api()

        try:
            _ = api_core.patch_namespaced_config_map(
                namespace=config_map_value_ref.namespace,
                name=config_map_value_ref.name,
                body={"data": {config_map_value_ref.key: value}},
            )
        except ApiException as error:
            msg = f"Exception when calling CoreV1Api->patch_namespaced_config_map: {error}"
            raise RuntimeError(msg) from error

        report.debug("Done")
