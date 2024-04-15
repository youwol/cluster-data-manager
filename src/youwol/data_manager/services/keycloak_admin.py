"""Main class and ancillary classes for keyclak client."""

# standard library
import datetime
import json
import urllib.request

from dataclasses import dataclass

# typing
from typing import Any, Optional

# relative
from .oidc_client import OidcClient, OidcClientConfig
from .reporting import Report


@dataclass(frozen=True, kw_only=True)
class KeycloakAdminCredentials:
    """Represent the credentials (realm, user and password) for keycloak client."""

    realm: str
    username: str
    password: str


class TokensManager:
    """Manage tokens.

    Take an OidcClient and username/password.
    Will refresh tokens on expiration, or request new tokens if refresh token itself has expired.

    Notes:
        Actually the expiration_threshold attribute (defaulting to 5 secondes) is used to force refreshing tokens
        about to expire, so that asking for a token return a token usable during that time.
    """

    def __init__(
        self,
        report: Report,
        username: str,
        password: str,
        oidc_client: OidcClient,
        expiration_threshold: int = 5,
    ):
        """Simple constructor.

        Args:
            report (Report): the report
            username (str): the account username for grant_password flow
            password (str): the account password for gront_password flow
            oidc_client (OidcClient): the openid connect client
            expiration_threshold (int): the expiration threshold (default to 5 seconds)
        """
        self._username = username
        self._password = password
        self._oidc_client = oidc_client
        self._access_token: Optional[str] = None
        self._access_token_expire_at: Optional[float] = None
        self._refresh_token: Optional[str] = None
        self._refresh_token_expire_at: Optional[float] = None
        self._expiration_threshold = expiration_threshold
        self._report = report.get_sub_report(
            task="TokensManager", init_status="ComponentInitialized"
        )

    def get_access_token(self) -> str:
        """Get an access token.

        If access token has expired or is about to (according to expiration_threshold), refresh tokens using the refresh
        token. If refresh_token itself has expired or is about to (again, according to expiration threshold), request
        new tokens using grant password.
        """
        report = self._report.get_sub_report(
            task="get_access_token", init_status="in function"
        )
        now = datetime.datetime.now().timestamp()
        if (
            self._access_token is None
            or self._access_token_expire_at is None
            or self._access_token_expire_at < now
        ):
            if (
                self._refresh_token is None
                or self._refresh_token_expire_at is None
                or self._refresh_token_expire_at < now
            ):
                report.notify("refresh_token missing or expired : need new tokens")
                self._grant_password_tokens()
            else:
                report.notify("access_token missing or expired : refreshing tokens")
                self._refresh_tokens()
        if self._access_token is None:
            raise RuntimeError("Unable to obtain access token")
        return self._access_token

    def _grant_password_tokens(self) -> None:
        report = self._report.get_sub_report(
            task="grant_password_tokens", init_status="in function"
        )

        report.debug("calling OidcClient")
        tokens = self._oidc_client.grant_password_tokens(self._username, self._password)

        report.debug("caching tokens")
        self._store_tokens(tokens)
        report.debug("done")

    def _refresh_tokens(self) -> None:
        report = self._report.get_sub_report(
            task="refresh_tokens", init_status="in function"
        )

        report.debug("calling OidcClient")
        if self._refresh_token is None:
            raise RuntimeError("Unable to refresh tokens, no refresh_token")
        tokens = self._oidc_client.refresh_tokens(self._refresh_token)

        report.debug("caching tokens")
        self._store_tokens(tokens)
        report.debug("done")

    def _store_tokens(self, tokens: Any) -> None:
        self._access_token = tokens["access_token"]
        self._refresh_token = tokens["refresh_token"]

        expire_from = datetime.datetime.now().timestamp() - self._expiration_threshold
        self._access_token_expire_at = expire_from + tokens["expires_in"]
        self._refresh_token_expire_at = expire_from + tokens["refresh_expires_in"]


class KeycloakAdmin:
    """Client for keycloak administration."""

    def __init__(
        self, report: Report, credentials: KeycloakAdminCredentials, base_url: str
    ):
        """Simple constructor.

        Args:
            report (Report): the report
            credentials (KeycloakAdminCredentials): the credentials for Keycloak administration
            base_url (str): the base url for Keycloak administration
        """
        sub_report = report.get_sub_report(
            task="KeycloakAdmin", init_status="ComponentInitialized"
        )
        self._base_url = base_url
        self._tokens_manager = TokensManager(
            report=sub_report,
            username=credentials.username,
            password=credentials.password,
            oidc_client=OidcClient(
                report=sub_report,
                oidc_client_config=OidcClientConfig(
                    client_id="admin-cli",
                    client_secret=None,
                    issuer=f"{base_url}/realms/{credentials.realm}",
                ),
            ),
        )
        self._report = sub_report

    def system_info(self) -> Any:
        """Retrieve keycloak instance system infos."""
        report = self._report.get_sub_report("system_info", init_status="in function")
        endpoint = f"{self._base_url}/admin/serverinfo"
        auth_header = {
            "Authorization": f"Bearer {self._tokens_manager.get_access_token()}"
        }
        report.debug(f"Calling endpoint {endpoint}")
        req = urllib.request.Request(url=endpoint, headers=auth_header)
        with urllib.request.urlopen(req) as resp:
            report.debug("decoding response")
            result = json.loads(resp.read().decode())
            report.set_status("exit function")
            return result["systemInfo"]
