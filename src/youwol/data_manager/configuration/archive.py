# standard library
from enum import Enum


class ArchiveItem(Enum):
    MINIO = "minio"
    CQL = "cql"
    KEYCLOAK = "kc"
    METADATA = "metadata.json"
