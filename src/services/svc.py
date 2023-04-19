"""Manage services instances.

Use get_<service>_builder() to obtain a nullary builder for a service.

Notes:
    It is possible to overload the definition of any service by using the context object before calling builders.
"""
from typing import Callable, Optional

from services import env
from services.archiver import Archiver
from services.cluster_maintenance import ClusterMaintenance, MaintenanceDetails
from services.cqlsh_commands import CqlInstance, CqlshCommands
from services.google_drive import GoogleDrive
from services.kubernetes_api import KubernetesApi, KubernetesConfigMapValueRef, KubernetesIngressRef
from services.mc_commands import McCommands, MinioClientPaths, MinioLocalInstance, S3Credentials, S3Instance
from services.oidc_client import OidcClient, OidcClientConfig
from services.reporting.reporting import Report, Reporting


# pylint: disable=too-many-instance-attributes
class Context:
    """Hold services instances."""
    cqlsh_commands: Optional[CqlshCommands] = None
    mc_commands: Optional[McCommands] = None
    report: Optional[Report] = None
    archiver: Optional[Archiver] = None
    oidc_client: Optional[OidcClient] = None
    google_drive: Optional[GoogleDrive] = None
    cluster_maintenance: Optional[ClusterMaintenance] = None
    kubernetes_api: Optional[KubernetesApi] = None


context = Context()


def get_report_builder() -> Callable[[], Report]:
    """Get a nullary builder for a configured instance of the report service.

    Returns:
        Callable[[], Reporting]: a nullary builder for the report service.
    """
    if context.report is not None:
        return lambda: context.report

    path_log_file = env.file(env.path_log_file)
    task_name = env.arg_task_name()

    def builder() -> Report:
        if context.report is None:
            context.report = Reporting(path_log_file=path_log_file, initial_task=task_name).get_root_report()
        return context.report

    return builder


def get_cqlsh_commands_builder() -> Callable[[], CqlshCommands]:
    """Get a nullary builder for a configured instance of the cqlsh_commands service.

    Returns:
        Callable[[], CqlshCommands]: a nullary builder for the cqlsh_commands service.
    """

    if context.cqlsh_commands is not None:
        return lambda: context.cqlsh_commands

    report_builder = get_report_builder()
    cqlsh_command = env.not_empty_string(env.cqlsh_command)
    cql_instance_host = env.maybe_string(env.cql_host)

    def builder() -> CqlshCommands:
        if context.cqlsh_commands is None:
            cql_instance = CqlInstance(host=cql_instance_host)
            context.cqlsh_commands = CqlshCommands(report=report_builder(),
                                                   instance=cql_instance,
                                                   cqlsh=cqlsh_command)
        return context.cqlsh_commands

    return builder


def get_mc_commands_builder() -> Callable[[], McCommands]:
    """Get a builder for a configured instance of the mc_commands service.

    Returns:
        Callable[[], McCommands]: a nullary builder for the mc_commands service.
    """

    if context.mc_commands is not None:
        return lambda: context.mc_commands

    report_builder = get_report_builder()
    path_mc = env.existing_path(env.path_mc)
    path_mc_config = env.existing_path(env.path_mc_config)
    local_access_key = env.not_empty_string(env.minio_local_access_key)
    local_secret_key = env.not_empty_string(env.minio_local_secret_key)
    local_port = env.integer(env.minio_local_port, 9000)

    def builder() -> McCommands:
        if context.mc_commands is None:
            local = MinioLocalInstance(
                access_key=local_access_key,
                secret_key=local_secret_key,
                port=local_port,
            )

            cluster = S3Instance(
                credentials=S3Credentials(
                    access_key=env.not_empty_string(env.s3_access_key),
                    secret_key=env.not_empty_string(env.s3_secret_key),
                ),
                host=env.not_empty_string(env.s3_host),
                port=env.integer(env.s3_port, 9000),
                tls=env.boolean(env.s3_tls, True),
            )

            mc_paths = MinioClientPaths(
                path_bin=path_mc,
                path_config=path_mc_config
            )

            context.mc_commands = McCommands(report=report_builder(),
                                             mc_paths=mc_paths,
                                             local=local,
                                             cluster=cluster)

        return context.mc_commands

    return builder


def get_oidc_client_builder() -> Callable[[], OidcClient]:
    """Get a builder for a configured instance of the Oidc client.

    Returns:
        Callable[[], OidcClient]: a nullary builder for the Oidc client
    """
    if context.oidc_client is not None:
        return lambda: context.oidc_client

    report_builder = get_report_builder()
    issuer = env.not_empty_string(env.oidc_issuer)
    client_id = env.not_empty_string(env.oidc_client_id)
    client_secret = env.not_empty_string(env.oidc_client_secret)

    def builder() -> OidcClient:
        if context.oidc_client is None:
            oidc_client_config = OidcClientConfig(issuer=issuer, client_id=client_id, client_secret=client_secret)
            context.oidc_client = OidcClient(report=report_builder(),
                                             oidc_client_config=oidc_client_config)
        return context.oidc_client

    return builder


def get_google_drive_builder() -> Callable[[], GoogleDrive]:
    """Get a builder for a configured instance of the google_drive service.

    Returns:
        Callable[[], GoogleDrive]: a nullary builder for the google_drive service.
    """

    if context.google_drive is not None:
        return lambda: context.google_drive

    report_builder = get_report_builder()
    oidc_client_builder = get_oidc_client_builder()
    drive_id = env.not_empty_string(env.google_drive_id)

    def builder() -> GoogleDrive:
        if context.google_drive is None:
            context.google_drive = GoogleDrive(report=report_builder(),
                                               drive_id=drive_id,
                                               oidc_client=oidc_client_builder())

        return context.google_drive

    return builder


def get_archiver_builder() -> Callable[[], Archiver]:
    """Get a builder for a configured instance of the archiver service.

    Return:
        Callable[[], Archiver]: a nullary builder for the archiver service.
    """

    if context.archiver is not None:
        return lambda: context.archiver

    report_builder = get_report_builder()
    path_work_dir = env.existing_path(env.path_work_dir)
    job_uuid = env.not_empty_string(env.job_uuid)

    def builder() -> Archiver:
        if context.archiver is None:
            context.archiver = Archiver(report=report_builder(), path_work_dir=path_work_dir, job_uuid=job_uuid)

        return context.archiver

    return builder


def get_cluster_maintenance_builder() -> Callable[[], ClusterMaintenance]:
    """Get a builder for a configured instance of the cluster_maintenance service.

    Returns:
        Callable[[], ClusterMaintenance]: a nullary builder for the cluster_maintenance service.
    """

    if context.cluster_maintenance is not None:
        return lambda: context.cluster_maintenance

    report_builder = get_report_builder()
    k8s_api_builder = get_kubernetes_api_builder()
    maintenance_namespace = env.not_empty_string(env.maintenance_namespace)
    maintenance_ingress_name = env.not_empty_string(env.maintenance_ingress_name)
    maintenance_ingress_class_name = env.not_empty_string(env.maintenance_ingress_class_name)
    maintenance_config_map_name = env.not_empty_string(env.maintenance_config_map_name)
    maintenance_config_map_key = env.not_empty_string(env.maintenance_config_map_key)
    maintenance_config_map_value = env.not_empty_string(env.maintenance_config_map_value)

    def builder() -> ClusterMaintenance:
        if context.cluster_maintenance is None:
            context.cluster_maintenance = ClusterMaintenance(
                report=report_builder(),
                k8s_api=k8s_api_builder(),
                maintenance_details=(MaintenanceDetails(
                    ingress_ref=(KubernetesIngressRef(
                        namespace=maintenance_namespace,
                        name=maintenance_ingress_name
                    )),
                    ingress_class_name=maintenance_ingress_class_name,
                    config_map_value_ref=(KubernetesConfigMapValueRef(
                        namespace=maintenance_namespace,
                        name=maintenance_config_map_name,
                        key=maintenance_config_map_key
                    )),
                    config_map_value=maintenance_config_map_value
                ))
            )

        return context.cluster_maintenance

    return builder


def get_kubernetes_api_builder() -> Callable[[], KubernetesApi]:
    """Get a builder for a configured instance of the kubernetes_api service.

    Returns:
        Callable[[], KubernetesApi]: a nullary builder for the kubernetes_api service.
    """

    if context.kubernetes_api is not None:
        return lambda: context.kubernetes_api

    report_builder = get_report_builder()

    def builder() -> KubernetesApi:
        if context.kubernetes_api is None:
            context.kubernetes_api = KubernetesApi(report=report_builder())

        return context.kubernetes_api

    return builder
