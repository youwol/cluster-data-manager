"""Main class and ancillary classes to request OIDC tokens."""
import json
import urllib.parse
import urllib.request
from typing import Any

from services.reporting import Report


class OidcClientConfig:
    """ Represent the configuration of an OIDC client."""

    def __init__(self, issuer: str, client_id: str, client_secret):
        self._issuer = issuer
        self._client_id = client_id
        self._client_secret = client_secret

    def issuer(self) -> str:
        """Simple getter.

        Returns:
            str: the issuer.
        """
        return self._issuer

    def client_id(self) -> str:
        """Simple getter.

        Returns:
            str: the client_id.
        """
        return self._client_id

    def client_secret(self) -> str:
        """Simple getter.

        Returns:
            str: the client_secret.
        """
        return self._client_secret


class OidcClient:
    """Oidc client."""

    def __init__(self, report: Report, oidc_client_config: OidcClientConfig):
        self._issuer_url = oidc_client_config.issuer()
        self._client_id = oidc_client_config.client_id()
        self._client_secret = oidc_client_config.client_secret()
        self._openid_configuration = None
        self._report = report.get_sub_report(task="KeycloakClient", init_status="Component Initialized")

    def grant_client_credentials_tokens(self) -> Any:
        """Grant client_credentials tokens.

        Returns:
            Any: the tokens.
        """
        report = self._report.get_sub_report(task="grant_client_credentials_tokens", init_status="in function")
        body = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "openid"
            }
        ).encode()
        req = urllib.request.Request(self._get_token_endpoint(), body)
        report.debug("calling endpoint")
        with urllib.request.urlopen(req) as resp:
            report.debug("decoding response")
            result = json.loads(resp.read().decode())
            report.set_status("exit function")
            return result

    def issuer(self) -> str:
        """Simple getter.

        Returns:
            str: the issuer url
        """
        return self._issuer_url

    def client_id(self) -> str:
        """Simple getter.

        Returns:
            str: the client_id.
        """
        return self._client_id

    def _get_token_endpoint(self):
        return self._get_oidc_configuration()["token_endpoint"]

    def _get_oidc_configuration(self):
        if self._openid_configuration is None:
            # NB: No cache invalidation since only call once for the lifetime of the application
            req = urllib.request.Request(self._get_oidc_well_known_url())
            with urllib.request.urlopen(req) as resp:
                self._openid_configuration = json.loads(resp.read().decode())

        return self._openid_configuration

    def _get_oidc_well_known_url(self):
        return f"{self._issuer_url}/.well-known/openid-configuration"
