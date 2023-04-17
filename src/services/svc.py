from pathlib import Path

from services import env


def get_report_builder():
    path_log_file = Path(env.not_empty_string(env.path_log_file))

    def builder():
        from services import svc_context
        if svc_context.report is None:
            from services.reporting.reporting import Reporting
            svc_context.report = Reporting(path_log_file=path_log_file, initial_task="Backup").get_root_report()
        return svc_context.report

    return builder


def get_cqlsh_commands_builder():
    report_builder = get_report_builder()
    cqlsh_command = env.not_empty_string(env.cqlsh_command)
    cql_instance_host = env.maybe_string(env.cql_host)

    def builder():
        from services import svc_context
        if svc_context.cqlsh_commands is None:
            from services.cqlsh_commands import CqlshCommands
            from services.cqlsh_commands import CqlInstance
            cql_instance = CqlInstance(host=cql_instance_host)
            svc_context.cqlsh_commands = CqlshCommands(report=report_builder(),
                                                       instance=cql_instance,
                                                       cqlsh=cqlsh_command)
        return svc_context.cqlsh_commands

    return builder


def get_mc_commands_builder():
    report_builder = get_report_builder()
    path_mc = env.existing_path(env.path_mc)
    path_mc_config = env.existing_path(env.path_mc_config)
    local_access_key = env.not_empty_string(env.minio_local_access_key)
    local_secret_key = env.not_empty_string(env.minio_local_secret_key)
    local_port = env.integer(env.minio_local_port, 9000)
    local_tls = env.boolean(env.minio_local_tls, False)

    def builder():
        from services import svc_context

        if svc_context.mc_commands is None:
            from services.mc_commands import McCommands
            from services.mc_commands import MinioLocalInstance
            from services.mc_commands import S3Instance

            local = MinioLocalInstance(
                access_key=local_access_key,
                secret_key=local_secret_key,
                port=local_port,
                tls=local_tls,
            )

            cluster = S3Instance(
                access_key=env.not_empty_string(env.s3_access_key),
                secret_key=env.not_empty_string(env.s3_secret_key),
                host=env.not_empty_string(env.s3_host),
                port=env.integer(env.s3_port, 9000),
                tls=env.boolean(env.s3_tls, True),
            )

            svc_context.mc_commands = McCommands(report=report_builder(),
                                                 path_mc=path_mc,
                                                 path_mc_config=path_mc_config,
                                                 local=local,
                                                 cluster=cluster)

        return svc_context.mc_commands

    return builder


def get_oidc_client_builder():
    report_builder = get_report_builder()
    issuer = env.not_empty_string(env.oidc_issuer)
    client_id = env.not_empty_string(env.oidc_client_id)
    client_secret = env.not_empty_string(env.oidc_client_secret)

    def builder():
        from services import svc_context
        if svc_context.oidc_client is None:
            from services.keycloak_client import KeycloakClient, OidcClientConfig
            oidc_client_config = OidcClientConfig(issuer=issuer, client_id=client_id, client_secret=client_secret)
            svc_context.oidc_client = KeycloakClient(report=report_builder(), oidc_client_config=oidc_client_config)

        return svc_context.oidc_client

    return builder


def get_google_drive_builder():
    report_builder = get_report_builder()
    oidc_client_builder = get_oidc_client_builder()
    drive_id = env.not_empty_string(env.google_drive_id)

    def builder():
        from services import svc_context
        if svc_context.google_drive is None:
            from services.google_drive import GoogleDrive
            svc_context.google_drive = GoogleDrive(report=report_builder(), drive_id=drive_id,
                                                   oidc_client=oidc_client_builder())

        return svc_context.google_drive

    return builder


def get_archiver_builder():
    report_builder = get_report_builder()
    path_work_dir = env.existing_path(env.path_work_dir)
    job_uuid = env.not_empty_string(env.job_uuid)

    def builder():
        from services import svc_context
        if svc_context.archiver is None:
            from services.archiver import Archiver
            svc_context.archiver = Archiver(report=report_builder(), path_work_dir=path_work_dir, job_uuid=job_uuid)

        return svc_context.archiver

    return builder


def get_cluster_maintenance_builder():
    report_builder = get_report_builder()
    k8s_api_builder = get_kubernetes_api_builder()
    maintenance_ingress_name = env.not_empty_string(env.maintenance_ingress_name)
    maintenance_ingress_namespace = env.not_empty_string(env.maintenance_ingress_namespace)
    maintenance_ingress_class_name = env.not_empty_string(env.maintenance_ingress_class_name)
    maintenance_config_map_name = env.not_empty_string(env.maintenance_config_map_name)
    maintenance_config_map_namespace = env.not_empty_string(env.maintenance_config_map_namespace)
    maintenance_config_map_key = env.not_empty_string(env.maintenance_config_map_key)
    maintenance_config_map_value = env.not_empty_string(env.maintenance_config_map_value)

    def builder():
        from services import svc_context
        if svc_context.cluster_maintenance is None:
            from .cluster_maintenance import ClusterMaintenance, MaintenanceDetails
            maintenance_details = MaintenanceDetails(
                ingress_name=maintenance_ingress_name,
                ingress_namespace=maintenance_ingress_namespace,
                ingress_class_name=maintenance_ingress_class_name,
                config_map_name=maintenance_config_map_name,
                config_map_namespace=maintenance_config_map_namespace,
                config_map_key=maintenance_config_map_key,
                config_map_value=maintenance_config_map_value
            )

            svc_context.cluster_maintenance = ClusterMaintenance(
                report=report_builder(),
                k8s_api=k8s_api_builder(),
                maintenance_details=maintenance_details
            )

        return svc_context.cluster_maintenance

    return builder


def get_kubernetes_api_builder():
    report_builder = get_report_builder()

    def builder():
        from services import svc_context
        if svc_context.kubernetes_api is None:
            from .kubernetes_api import KubernetesApi
            svc_context.kubernetes_api = KubernetesApi(report=report_builder())

        return svc_context.kubernetes_api

    return builder
