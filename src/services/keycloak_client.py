import urllib.parse
import urllib.request

from services.reporting import Report


class OidcClientConfig:

    def __init__(self, issuer: str, client_id: str, client_secret):
        self._issuer = issuer
        self._client_id = client_id
        self._client_secret = client_secret

    def get_issuer(self):
        return self._issuer

    def get_client_id(self):
        return self._client_id

    def get_client_secret(self):
        return self._client_secret


class KeycloakClient:

    def __init__(self, report: Report, oidc_client_config: OidcClientConfig):
        self._keycloak_issuer_url = oidc_client_config.get_issuer()
        self._client_id = oidc_client_config.get_client_id()
        self._client_secret = oidc_client_config.get_client_secret()
        self._report = report.get_sub_report(task="KeycloakClient", init_status="Component Initialized")

    def service_account_tokens(self) -> str:
        report = self._report.get_sub_report(task="service_account_tokens", init_status="in function")
        body = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "openid"
            }
        ).encode()
        req = urllib.request.Request(self._get_oidc_token_url(), body)
        report.debug("calling endpoint")
        resp = urllib.request.urlopen(req)
        report.debug("decoding response")
        result = resp.read().decode()
        report.set_status("exit function")
        return result

    def _get_oidc_token_url(self):
        return f"{self._keycloak_issuer_url}/protocol/openid-connect/token"
