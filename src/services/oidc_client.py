"""Main class and ancillary classes to request OIDC tokens."""
# standard library
import json
import urllib.parse
import urllib.request

from dataclasses import dataclass

# typing
from typing import Any, Optional

# relative
from .reporting import Report


@dataclass(frozen=True, kw_only=True)
class OidcClientConfig:
    """Represent the configuration of an OIDC client."""

    issuer: str
    client_id: str
    client_secret: Optional[str]


class OidcClient:
    """Oidc client."""

    def __init__(self, report: Report, oidc_client_config: OidcClientConfig):
        """Simple constructor.

        Args:
            report (Report): the report
            oidc_client_config (OidcClientConfig): the client configuration
        """
        self._issuer_url = oidc_client_config.issuer
        self._client_id = oidc_client_config.client_id
        self._client_secret = oidc_client_config.client_secret
        self._openid_configuration = None
        self._report = report.get_sub_report(
            task="OidcClient", init_status="Component Initialized"
        )

    def grant_client_credentials_tokens(self) -> Any:
        """Grant client_credentials tokens.

        Returns:
            Any: the tokens.
        """
        report = self._report.get_sub_report(
            task="grant_client_credentials_tokens", init_status="in function"
        )
        params = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "scope": "openid",
        }
        if self._client_secret is not None:
            params["client_secret"] = self._client_secret

        req = urllib.request.Request(
            self._get_token_endpoint(), urllib.parse.urlencode(params).encode()
        )
        report.debug("calling endpoint")
        with urllib.request.urlopen(req) as resp:
            report.debug("decoding response")
            result = json.loads(resp.read().decode())
            report.set_status("exit function")
            return result

    def grant_password_tokens(self, username: str, password: str) -> Any:
        """Grant password tokens.

        Returns:
            Any: the tokens.
        """
        report = self._report.get_sub_report(
            task="grant_password_tokens", init_status="in function"
        )
        params = {
            "grant_type": "password",
            "client_id": self._client_id,
            "scope": "openid",
            "username": username,
            "password": password,
        }
        if self._client_secret is not None:
            params["client_secret"] = self._client_secret

        req = urllib.request.Request(
            self._get_token_endpoint(), urllib.parse.urlencode(params).encode()
        )
        report.debug("calling endpoint")
        with urllib.request.urlopen(req) as resp:
            report.debug("decoding response")
            result = json.loads(resp.read().decode())
            report.set_status("exit function")
            return result

    def refresh_tokens(self, refresh_token: str) -> Any:
        """Refresh tokens.

        Args:
            refresh_token (str): the refresh token (must not have been expired)

        Returns:
            Any: fresh tokens.
        """
        report = self._report.get_sub_report(
            task="refresh_tokens", init_status="in function"
        )
        params = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "scope": "openid",
            "refresh_token": refresh_token,
        }
        if self._client_secret is not None:
            params["client_secret"] = self._client_secret

        req = urllib.request.Request(
            self._get_token_endpoint(), urllib.parse.urlencode(params).encode()
        )
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

    def _get_token_endpoint(self) -> str:
        return str(self._get_oidc_configuration()["token_endpoint"])

    def _get_oidc_configuration(self) -> Any:
        if self._openid_configuration is None:
            # NB: No cache invalidation since only call once for the lifetime of the application
            req = urllib.request.Request(self._get_oidc_well_known_url())
            with urllib.request.urlopen(req) as resp:
                self._openid_configuration = json.loads(resp.read().decode())

        return self._openid_configuration

    def _get_oidc_well_known_url(self) -> str:
        return f"{self._issuer_url}/.well-known/openid-configuration"
