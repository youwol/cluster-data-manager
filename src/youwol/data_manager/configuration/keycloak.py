# standard library
from enum import Enum


class KeycloakStatus(Enum):
    SETUP = "SETUP"
    DONE = "DONE"
    ERROR = "ERROR"
