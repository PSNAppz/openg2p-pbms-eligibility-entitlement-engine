import base64
from datetime import datetime, timedelta, timezone

import httpx
import orjson


class KeymanagerHelper:
    def __init__(self, config, logger):
        self._config = config
        self._logger = logger
        self._keymanager_auth_token = None
        self._keymanager_auth_token_expiry = None

    @staticmethod
    def urlsafe_b64encode(data: bytes) -> str:
        """Base64-url encode the given bytes, stripping any trailing '='."""
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def get_current_isotimestamp() -> str:
        """Return the current UTC time in ISO 8601 format with 'Z'."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    async def create_jwt_token(
        self,
        payload,
        expiration_minutes=60,
        include_payload=False,
        include_certificate=False,
        include_cert_hash=False,
    ) -> str:
        if isinstance(payload, dict):
            payload_bytes = orjson.dumps(payload)
        elif isinstance(payload, str):
            payload_bytes = payload.encode()
        else:
            payload_bytes = payload

        cookies = {}
        if getattr(self._config, "keymanager_auth_enabled", False):
            self._logger.debug(
                "Setting Authorization Cookie from Keymananger Auth Service"
            )
            cookies["Authorization"] = await self.get_keymanager_auth_token()
        current_time = self.get_current_isotimestamp()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._config.keymanager_api_base_url}/jwtSign",
                json={
                    "id": "string",
                    "version": "string",
                    "requesttime": current_time,
                    "metadata": {},
                    "request": {
                        "dataToSign": self.urlsafe_b64encode(payload_bytes),
                        "applicationId": getattr(
                            self._config, "sign_key_keymanager_app_id", ""
                        )
                        or "",
                        "referenceId": getattr(
                            self._config, "sign_key_keymanager_ref_id", ""
                        )
                        or "",
                        "includePayload": include_payload,
                        "includeCertificate": include_certificate,
                        "includeCertHash": include_cert_hash,
                    },
                },
                cookies=cookies,
                timeout=getattr(self._config, "keymanager_api_timeout", 10),
            )
        self._logger.debug("Keymanager JWT Sign API response: %s", response.text)
        response.raise_for_status()
        return ((response.json() or {}).get("response") or {}).get("jwtSignedData")

    async def get_keymanager_auth_token(self):
        if (
            self._keymanager_auth_token
            and self._keymanager_auth_token_expiry
            and self._keymanager_auth_token_expiry > datetime.now(timezone.utc)
        ):
            return self._keymanager_auth_token
        url = self._config.keymanager_auth_url
        payload = {
            "client_id": self._config.keymanager_auth_client_id,
            "client_secret": self._config.keymanager_auth_client_secret,
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=payload,
                timeout=getattr(self._config, "keymanager_api_timeout", 10),
            )
        response_data = response.json()
        expires_in = response_data.get("expires_in", 900)
        self._keymanager_auth_token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in
        )
        self._keymanager_auth_token = response_data["access_token"]
        return self._keymanager_auth_token
