"""Enumeration of the environments variables names."""
# standard library
from enum import Enum


class EnvironmentVars(Enum):
    pass


class ContainerImageEnvironmentVars(EnvironmentVars):
    """Environment variables names."""

    # All Jobs
    PATH_WORK_DIR = "PATH_WORK_DIR"
    PATH_LOG_FILE = "PATH_LOG_FILE"

    # Service CQL
    CQLSH_COMMAND = "CQLSH_COMMAND"

    # Service Minio
    PATH_MC = "PATH_MINIO_CLIENT"
    PATH_MC_CONFIG = "PATH_MINIO_CLIENT_CONFIG"

    # Service Keycloak
    PATH_KEYCLOAK_STATUS_FILE = "PATH_KEYCLOAK_STATUS_FILE"
    PATH_KEYCLOAK_SCRIPT = "PATH_KEYCLOAK_SCRIPT"


class DeploymentEnvironmentVars(EnvironmentVars):
    """Environment variables names defined when deploying"""

    # Service Cluster Maintenance
    MAINTENANCE_NAMESPACE = "MAINTENANCE_NAMESPACE"
    MAINTENANCE_INGRESS_NAME = "MAINTENANCE_INGRESS_NAME"
    MAINTENANCE_INGRESS_CLASS_NAME = "MAINTENANCE_INGRESS_CLASS_NAME"
    MAINTENANCE_CONFIG_MAP_NAME = "MAINTENANCE_CONFIG_MAP_NAME"
    MAINTENANCE_CONFIG_MAP_KEY = "MAINTENANCE_CONFIG_MAP_KEY"
    MAINTENANCE_CONFIG_MAP_VALUE = "MAINTENANCE_CONFIG_MAP_VALUE"

    # Service Kubernetes API
    # If not set, library kubernetes will use the mounted service account token.
    MAINTENANCE_KUBE_CONFIG = "MAINTENANCE_KUBE_CONFIG"
    MAINTENANCE_KUBE_CONFIG_CONTEXT = "MAINTENANCE_KUBE_CONFIG_CONTEXT"

    # Service CQL
    CQL_HOST = "CQL_HOST"

    # Service Minio
    # Minio local instance
    MINIO_LOCAL_ACCESS_KEY = "MINIO_LOCAL_ACCESS_KEY"
    MINIO_LOCAL_SECRET_KEY = "MINIO_LOCAL_SECRET_KEY"
    MINIO_LOCAL_PORT = "MINIO_LOCAL_PORT"
    # S3 instance
    S3_ACCESS_KEY = "S3_ACCESS_KEY"
    S3_SECRET_KEY = "S3_SECRET_KEY"
    S3_HOST = "S3_HOST"
    S3_TLS = "S3_TLS"
    S3_PORT = "S3_PORT"

    # Service Google Drive
    GOOGLE_DRIVE_ID = "GOOGLE_DRIVE_ID"
    # OIDC for Google Drive
    OIDC_ISSUER = "OIDC_ISSUER"
    OIDC_CLIENT_ID = "OIDC_CLIENT_ID"
    OIDC_CLIENT_SECRET = "OIDC_CLIENT_SECRET"

    # Service Keycloak
    KEYCLOAK_USERNAME = "KEYCLOAK_USERNAME"
    KEYCLOAK_PASSWORD = "KEYCLOAK_PASSWORD"
    KEYCLOAK_BASE_URL = "KEYCLOAK_BASE_URL"


class JobEnvironmentVars(EnvironmentVars):
    """Environment variables names for job parameters"""

    # All Tasks
    # Taken from k8s CronJob metadata (downward API)
    JOB_UUID = "JOB_UUID"
    # Folder in Google Drive, either “cron" or “manual”
    TYPE_BACKUP = "TYPE_BACKUP"

    # Job Restoration
    # Default to “latest” if not set
    RESTORE_ARCHIVE_NAME = "RESTORE_ARCHIVE_NAME"

    # Task CQL
    CQL_KEYSPACES = "CQL_KEYSPACES"
    CQL_TABLES = "CQL_TABLES"

    # Task S3
    S3_BUCKETS = "S3_BUCKETS"
