"""Manage services instances.

Use get_<service>_builder() to obtain a nullary builder for a service.

Notes:
    It is possible to overload the definition of any service by using the context object before calling builders.
"""
# typing
from typing import Callable, Optional

# application configuration
from youwol.data_manager.configuration import ConfigEnvVars, env_utils

# relative
from .archiver import Archiver
from .cluster_maintenance import ClusterMaintenance, MaintenanceDetails
from .containers_readiness import ContainersReadiness, ProbeKeycloak, ProbeMinio
from .cqlsh_commands import CqlInstance, CqlshCommands
from .google_drive import GoogleDrive
from .kubernetes_api import (
    KubernetesApi,
    KubernetesConfigMapValueRef,
    KubernetesIngressRef,
)
from .mc_commands import (
    McCommands,
    MinioClientPaths,
    MinioLocalInstance,
    S3Credentials,
    S3Instance,
)
from .oidc_client import OidcClient, OidcClientConfig
from .reporting.reporting import Report, Reporting


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
    containers_readiness: Optional[ContainersReadiness] = None


context = Context()


def get_report_builder() -> Callable[[], Report]:
    """Get a nullary builder for a configured instance of the report service.

    Returns:
        Callable[[], Reporting]: a nullary builder for the report service.
    """
    if context.report is not None:
        report = context.report
        return lambda: report

    path_log_file = env_utils.file(ConfigEnvVars.PATH_LOG_FILE)
    task_name = env_utils.arg_task_name()

    def builder() -> Report:
        if context.report is None:
            context.report = Reporting(
                path_log_file=path_log_file, initial_task=task_name
            ).get_root_report()
        return context.report

    return builder


def get_cqlsh_commands_builder() -> Callable[[], CqlshCommands]:
    """Get a nullary builder for a configured instance of the cqlsh_commands service.

    Returns:
        Callable[[], CqlshCommands]: a nullary builder for the cqlsh_commands service.
    """
    if context.cqlsh_commands is not None:
        cqlsh_commands = context.cqlsh_commands
        return lambda: cqlsh_commands

    report_builder = get_report_builder()
    cqlsh_command = env_utils.not_empty_string(ConfigEnvVars.CQLSH_COMMAND)
    cql_instance_host = env_utils.maybe_string(ConfigEnvVars.CQL_HOST)

    def builder() -> CqlshCommands:
        if context.cqlsh_commands is None:
            cql_instance = CqlInstance(host=cql_instance_host)
            context.cqlsh_commands = CqlshCommands(
                report=report_builder(), cql_instance=cql_instance, cqlsh=cqlsh_command
            )
        return context.cqlsh_commands

    return builder


def get_mc_commands_builder() -> Callable[[], McCommands]:
    """Get a builder for a configured instance of the mc_commands service.

    Returns:
        Callable[[], McCommands]: a nullary builder for the mc_commands service.
    """
    if context.mc_commands is not None:
        mc_commands = context.mc_commands
        return lambda: mc_commands

    report_builder = get_report_builder()
    path_mc = env_utils.existing_path(ConfigEnvVars.PATH_MC)
    path_mc_config = env_utils.empty_dir(ConfigEnvVars.PATH_MC_CONFIG)
    local_access_key = env_utils.not_empty_string(ConfigEnvVars.MINIO_LOCAL_ACCESS_KEY)
    local_secret_key = env_utils.not_empty_string(ConfigEnvVars.MINIO_LOCAL_SECRET_KEY)
    local_port = env_utils.integer(ConfigEnvVars.MINIO_LOCAL_PORT, 9000)
    s3_access_key = env_utils.not_empty_string(ConfigEnvVars.S3_ACCESS_KEY)
    s3_secret_key = env_utils.not_empty_string(ConfigEnvVars.S3_SECRET_KEY)
    s3_host = env_utils.not_empty_string(ConfigEnvVars.S3_HOST)
    s3_port = env_utils.integer(ConfigEnvVars.S3_PORT, 9000)
    s3_tls = env_utils.boolean(ConfigEnvVars.S3_TLS, True)

    def builder() -> McCommands:
        if context.mc_commands is None:
            local = MinioLocalInstance(
                access_key=local_access_key,
                secret_key=local_secret_key,
                port=local_port,
            )

            cluster = S3Instance(
                credentials=S3Credentials(
                    access_key=s3_access_key,
                    secret_key=s3_secret_key,
                ),
                host=s3_host,
                port=s3_port,
                tls=s3_tls,
            )

            mc_paths = MinioClientPaths(path_bin=path_mc, path_config=path_mc_config)

            context.mc_commands = McCommands(
                report=report_builder(),
                mc_paths=mc_paths,
                minio_instance=local,
                s3_instance=cluster,
            )

        return context.mc_commands

    return builder


def get_oidc_client_builder() -> Callable[[], OidcClient]:
    """Get a builder for a configured instance of the Oidc client.

    Returns:
        Callable[[], OidcClient]: a nullary builder for the Oidc client
    """
    if context.oidc_client is not None:
        oidc_client = context.oidc_client
        return lambda: oidc_client

    report_builder = get_report_builder()
    issuer = env_utils.not_empty_string(ConfigEnvVars.OIDC_ISSUER)
    client_id = env_utils.not_empty_string(ConfigEnvVars.OIDC_CLIENT_ID)
    client_secret = env_utils.not_empty_string(ConfigEnvVars.OIDC_CLIENT_SECRET)

    def builder() -> OidcClient:
        if context.oidc_client is None:
            oidc_client_config = OidcClientConfig(
                issuer=issuer, client_id=client_id, client_secret=client_secret
            )
            context.oidc_client = OidcClient(
                report=report_builder(), oidc_client_config=oidc_client_config
            )
        return context.oidc_client

    return builder


def get_google_drive_builder() -> Callable[[], GoogleDrive]:
    """Get a builder for a configured instance of the google_drive service.

    Returns:
        Callable[[], GoogleDrive]: a nullary builder for the google_drive service.
    """
    if context.google_drive is not None:
        google_drive = context.google_drive
        return lambda: google_drive

    report_builder = get_report_builder()
    oidc_client_builder = get_oidc_client_builder()
    drive_id = env_utils.not_empty_string(ConfigEnvVars.GOOGLE_DRIVE_ID)

    def builder() -> GoogleDrive:
        if context.google_drive is None:
            context.google_drive = GoogleDrive(
                report=report_builder(),
                drive_id=drive_id,
                oidc_client=oidc_client_builder(),
            )

        return context.google_drive

    return builder


def get_archiver_builder() -> Callable[[], Archiver]:
    """Get a builder for a configured instance of the archiver service.

    Return:
        Callable[[], Archiver]: a nullary builder for the archiver service.
    """
    if context.archiver is not None:
        archiver = context.archiver
        return lambda: archiver

    report_builder = get_report_builder()
    path_work_dir = env_utils.existing_path(ConfigEnvVars.PATH_WORK_DIR)
    job_uuid = env_utils.not_empty_string(ConfigEnvVars.JOB_UUID)

    def builder() -> Archiver:
        if context.archiver is None:
            context.archiver = Archiver(
                report=report_builder(), path_work_dir=path_work_dir, job_uuid=job_uuid
            )

        return context.archiver

    return builder


def get_cluster_maintenance_builder() -> Callable[[], ClusterMaintenance]:
    """Get a builder for a configured instance of the cluster_maintenance service.

    Returns:
        Callable[[], ClusterMaintenance]: a nullary builder for the cluster_maintenance service.
    """
    if context.cluster_maintenance is not None:
        cluster_maintenance = context.cluster_maintenance
        return lambda: cluster_maintenance

    report_builder = get_report_builder()
    k8s_api_builder = get_kubernetes_api_builder()
    maintenance_namespace = env_utils.not_empty_string(
        ConfigEnvVars.MAINTENANCE_NAMESPACE
    )
    maintenance_ingress_name = env_utils.not_empty_string(
        ConfigEnvVars.MAINTENANCE_INGRESS_NAME
    )
    maintenance_ingress_class_name = env_utils.not_empty_string(
        ConfigEnvVars.MAINTENANCE_INGRESS_CLASS_NAME
    )
    maintenance_config_map_name = env_utils.not_empty_string(
        ConfigEnvVars.MAINTENANCE_CONFIG_MAP_NAME
    )
    maintenance_config_map_key = env_utils.not_empty_string(
        ConfigEnvVars.MAINTENANCE_CONFIG_MAP_KEY
    )
    maintenance_config_map_value = env_utils.not_empty_string(
        ConfigEnvVars.MAINTENANCE_CONFIG_MAP_VALUE
    )

    def builder() -> ClusterMaintenance:
        if context.cluster_maintenance is None:
            context.cluster_maintenance = ClusterMaintenance(
                report=report_builder(),
                k8s_api=k8s_api_builder(),
                maintenance_details=(
                    MaintenanceDetails(
                        ingress_ref=(
                            KubernetesIngressRef(
                                namespace=maintenance_namespace,
                                name=maintenance_ingress_name,
                            )
                        ),
                        ingress_class_name=maintenance_ingress_class_name,
                        config_map_value_ref=(
                            KubernetesConfigMapValueRef(
                                namespace=maintenance_namespace,
                                name=maintenance_config_map_name,
                                key=maintenance_config_map_key,
                            )
                        ),
                        config_map_value=maintenance_config_map_value,
                    )
                ),
            )

        return context.cluster_maintenance

    return builder


def get_kubernetes_api_builder() -> Callable[[], KubernetesApi]:
    """Get a builder for a configured instance of the kubernetes_api service.

    Returns:
        Callable[[], KubernetesApi]: a nullary builder for the kubernetes_api service.
    """
    if context.kubernetes_api is not None:
        kubernetes_api = context.kubernetes_api
        return lambda: kubernetes_api

    report_builder = get_report_builder()
    kube_config = env_utils.maybe_string(ConfigEnvVars.MAINTENANCE_KUBE_CONFIG)
    kube_config_context = env_utils.maybe_string(
        ConfigEnvVars.MAINTENANCE_KUBE_CONFIG_CONTEXT
    )

    def builder() -> KubernetesApi:
        if context.kubernetes_api is None:
            context.kubernetes_api = KubernetesApi(
                report=report_builder(),
                kube_config=kube_config,
                kube_config_context=kube_config_context,
            )

        return context.kubernetes_api

    return builder


def get_containers_readiness_kc_and_minio_builder() -> (
    Callable[[], ContainersReadiness]
):
    """Get a builder for a configured instance of the containers readiness service.

    Returns:
        Callable[[], ContainersReadiness]: a nullary builder for the containers readiness service.
    """
    if context.containers_readiness is not None:
        containers_readiness = context.containers_readiness
        return lambda: containers_readiness

    report_builder = get_report_builder()
    path_keycloak_status_file = env_utils.existing_path(
        ConfigEnvVars.PATH_KEYCLOAK_STATUS_FILE
    )
    local_access_key = env_utils.not_empty_string(ConfigEnvVars.MINIO_LOCAL_ACCESS_KEY)
    local_secret_key = env_utils.not_empty_string(ConfigEnvVars.MINIO_LOCAL_SECRET_KEY)
    local_port = env_utils.integer(ConfigEnvVars.MINIO_LOCAL_PORT, 9000)

    def builder() -> ContainersReadiness:
        if context.containers_readiness is None:
            probe_keycloak = ProbeKeycloak(
                report=report_builder(),
                path_keycloak_status_file=path_keycloak_status_file,
            )
            minio_local_instance = MinioLocalInstance(
                access_key=local_access_key,
                secret_key=local_secret_key,
                port=local_port,
            )
            probe_minio = ProbeMinio(
                report=report_builder(), s3_instance=minio_local_instance
            )
            context.containers_readiness = ContainersReadiness(
                report=report_builder(), probes=[probe_keycloak, probe_minio]
            )

        return context.containers_readiness

    return builder


def get_containers_readiness_minio_builder() -> Callable[[], ContainersReadiness]:
    """Get a builder for a configured instance of the containers readiness service.

    Returns:
        Callable[[], ContainersReadiness]: a nullary builder for the containers readiness service.
    """
    if context.containers_readiness is not None:
        containers_readiness = context.containers_readiness
        return lambda: containers_readiness

    report_builder = get_report_builder()
    local_access_key = env_utils.not_empty_string(ConfigEnvVars.MINIO_LOCAL_ACCESS_KEY)
    local_secret_key = env_utils.not_empty_string(ConfigEnvVars.MINIO_LOCAL_SECRET_KEY)
    local_port = env_utils.integer(ConfigEnvVars.MINIO_LOCAL_PORT, 9000)

    def builder() -> ContainersReadiness:
        if context.containers_readiness is None:
            minio_local_instance = MinioLocalInstance(
                access_key=local_access_key,
                secret_key=local_secret_key,
                port=local_port,
            )
            probe_minio = ProbeMinio(
                report=report_builder(), s3_instance=minio_local_instance
            )
            context.containers_readiness = ContainersReadiness(
                report=report_builder(), probes=[probe_minio]
            )

        return context.containers_readiness

    return builder
