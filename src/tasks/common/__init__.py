"""Generalised code for tasks."""
from .cassandra import Cassandra as CommonCassandra
from .keycloak import Keycloak as CommonKeycloak
from .s3 import S3 as CommonS3
from .task import OnPathDirMissing

__all__ = ['CommonCassandra', 'CommonS3', 'CommonKeycloak', 'OnPathDirMissing']
