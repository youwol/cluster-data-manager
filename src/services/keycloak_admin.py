"""Main class and ancillary classes for keyclak client"""
import datetime
import json
import urllib.request
from typing import Any

from services.oidc_client import OidcClient, OidcClientConfig
from services.reporting import Report


class KeycloakAdminCredentials:
    """Represent the credentials (realm, user and password) for keycloak client"""

    def __init__(self, realm: str, username: str, password: str):
        self._realm = realm
        self._username = username
        self._password = password

    def realm(self) -> str:
        """Simple getter

        Returns:
            str: the realm
        """
        return self._realm

    def username(self) -> str:
        """Simple getter

        Returns:
            str: the username
        """
        return self._username

    def password(self) -> str:
        """Simple getter

        Returns:
            str: the password
        """
        return self._password


class TokensManager:
    """Manage tokens.

    Take an OidcClient and username/password.
    Will refresh tokens on expiration, or request new tokens if refresh token itself has expired.
    """

    def __init__(
            self,
            report: Report,
            username: str,
            password: str,
            oidc_client: OidcClient,
            expiration_threshold: int = 5
    ):
        self._username = username
        self._password = password
        self._oidc_client = oidc_client
        self._access_token = None
        self._access_token_expire_at = None
        self._refresh_token = None
        self._refresh_token_expire_at = None
        self._expiration_threshold = expiration_threshold
        self._report = report.get_sub_report(task="TokensManager", init_status="ComponentInitialized")

    def get_access_token(self):
        """Get an access token.

        If access token has expired, refresh tokens using the refresh token.
        If refresh_token itself has expired, request new tokens using grant password.
        """
        report = self._report.get_sub_report(task="get_access_token", init_status="in function")
        if self._access_token is None \
                or self._access_token_expire_at is None \
                or self._access_token_expire_at < datetime.datetime.now().timestamp():
            if self._refresh_token is None or \
                    self._refresh_token_expire_at < datetime.datetime.now().timestamp():
                report.notify("refresh_token missing or expired : need new tokens")
                self._grant_password_tokens()
            else:
                report.notify("access_token missing or expired : refreshing tokens")
                self._refresh_tokens()
        return self._access_token

    def _grant_password_tokens(self):
        report = self._report.get_sub_report(task="grant_password_tokens", init_status="in function")

        report.debug("calling OidcClient")
        tokens = self._oidc_client.grant_password_tokens(self._username, self._password)

        report.debug("caching tokens")
        self._store_tokens(tokens)
        report.debug("done")

    def _refresh_tokens(self):
        report = self._report.get_sub_report(task="refresh_tokens", init_status="in function")
        report.debug("calling OidcClient")
        tokens = self._oidc_client.refresh_tokens(self._refresh_token)

        report.debug("caching tokens")
        self._store_tokens(tokens)
        report.debug("done")

    def _store_tokens(self, tokens: Any):
        threshold = self._expiration_threshold
        self._access_token = tokens["access_token"]
        self._access_token_expire_at = datetime.datetime.now().timestamp() + tokens["expires_in"] - threshold
        self._refresh_token = tokens["refresh_token"]
        self._refresh_token_expire_at = datetime.datetime.now().timestamp() + tokens["refresh_expires_in"] - threshold


class KeycloakAdmin:
    """Client for keycloak administration"""

    def __init__(self, report: Report,
                 credentials: KeycloakAdminCredentials,
                 base_url: str = "http://localhost:8080/auth"):
        sub_report = report.get_sub_report(task="KeycloakAdmin", init_status="ComponentInitialized")
        self._base_url = base_url
        self._tokens_manager = TokensManager(
            report=sub_report,
            username=credentials.username(),
            password=credentials.password(),
            oidc_client=OidcClient(
                report=sub_report,
                oidc_client_config=OidcClientConfig(
                    client_id="admin-cli",
                    client_secret=None,
                    issuer=f"{base_url}/realms/{credentials.realm()}"
                )
            )
        )
        self._report = sub_report

    def system_info(self):
        """Retrieve keycloak instance system infos."""
        report = self._report.get_sub_report("system_info", init_status="in function")
        endpoint = f"{self._base_url}/admin/serverinfo"
        header = {"Authorization": f"Bearer {self._tokens_manager.get_access_token()}"}
        report.debug(f"Calling endpoint {endpoint}")
        req = urllib.request.Request(url=endpoint, headers=header)
        with urllib.request.urlopen(req) as resp:
            report.debug("decoding response")
            result = json.loads(resp.read().decode())
            report.set_status("exit function")
            return result["systemInfo"]
