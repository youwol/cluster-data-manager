# relative
from ..common import CommonKeycloak
from .task import RestoreSubtask


class Keycloak(CommonKeycloak, RestoreSubtask):
    """No implementation needed"""
