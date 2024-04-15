"""Services module.

Use the various factories to obtain nullary builder for a correctly configured service instances,
i.e. get_<service>_builder() will return a nullary builder for building a configured instance of service <service>.
"""

# relative
from .builder import get_archiver_builder as get_service_archiver_builder
from .builder import (
    get_containers_readiness_builder as get_service_containers_readiness_builder,
)
from .builder import (
    get_context_maintenance_builder as get_service_context_maintenance_builder,
)
from .builder import get_cqlsh_commands_builder as get_service_cqlsh_commands_builder
from .builder import get_google_drive_builder as get_service_google_drive_builder
from .builder import get_kubernetes_api_builder as get_service_kubernetes_api_builder
from .builder import get_mc_commands_builder as get_service_mc_commands_builder
from .builder import get_oidc_client_builder as get_service_oidc_client_builder
from .builder import get_report_builder as get_service_report_builder

__all__ = [
    "get_service_report_builder",
    "get_service_oidc_client_builder",
    "get_service_kubernetes_api_builder",
    "get_service_mc_commands_builder",
    "get_service_google_drive_builder",
    "get_service_context_maintenance_builder",
    "get_service_cqlsh_commands_builder",
    "get_service_archiver_builder",
    "get_service_containers_readiness_builder",
]
