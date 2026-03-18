from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from src.config.settings import Settings
from src.domain.digi import Digi


@dataclass(frozen=True)
class DigiOperationResult:
    success: bool
    message: str
    data: dict[str, Any] | None = None


class DigiService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = self._settings.digi_timeout_seconds

    def _build_auth(
        self,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> HTTPBasicAuth:
        user = digi_user.strip() if digi_user and digi_user.strip() else self._settings.digi_user
        password = digi_pass if digi_pass and digi_pass.strip() else self._settings.digi_pass
        return HTTPBasicAuth(user, password)

    def _build_url(self, endpoint: str) -> str:
        return f"{self._settings.digi_base_url}/{endpoint.lstrip('/')}"

    def _get(
        self,
        endpoint: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> requests.Response:
        url = self._build_url(endpoint)
        response = requests.get(
            url,
            auth=self._build_auth(digi_user, digi_pass),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response

    def _post_xml(
        self,
        endpoint: str,
        payload: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> requests.Response:
        url = self._build_url(endpoint)
        headers = {
            "Content-Type": "application/xml",
        }
        response = requests.post(
            url,
            data=payload.encode("utf-8"),
            headers=headers,
            auth=self._build_auth(digi_user, digi_pass),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response

    def _map_device_to_domain(self, device_data: dict[str, Any]) -> Digi:
        return Digi(
            id=device_data.get("id"),
            customer_id=device_data.get("customer_id"),
            d_type=device_data.get("type"),
            description=device_data.get("description"),
            ip=device_data.get("ip"),
            name=device_data.get("name"),
            location=device_data.get("location"),
            connection_status=device_data.get("connection_status"),
        )

    def search_device_by_ip(
        self,
        ip: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> Digi | None:
        endpoint = f"{self._settings.digi_search_node_by_ip}'{ip}'"

        response = self._get(
            endpoint,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )
        payload = response.json()

        devices = payload.get("list", [])
        if not devices:
            return None

        first_device = devices[0]
        return self._map_device_to_domain(first_device)

    def get_device_by_id(
        self,
        device_id: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> Digi | None:
        endpoint = f"{self._settings.digi_search_node_by_id}{device_id}"

        response = self._get(
            endpoint,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )
        payload = response.json()

        if not payload:
            return None

        return self._map_device_to_domain(payload)

    def get_connection_status_by_id(
        self,
        device_id: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> str | None:
        device = self.get_device_by_id(
            device_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )
        if not device:
            return None
        return device.connection_status

    def update_system_location(
        self,
        device_id: str,
        new_location: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> DigiOperationResult:
        payload = f"""<sci_request version="1.0">
  <send_message>
    <targets>
      <device id="{device_id}"/>
    </targets>
    <rci_request version="1.1">
      <set_setting>
        <system>
          <location>{new_location}</location>
        </system>
      </set_setting>
    </rci_request>
  </send_message>
</sci_request>"""

        try:
            response = self._post_xml(
                self._settings.digi_sci_api,
                payload,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            return DigiOperationResult(
                success=True,
                message="System location updated successfully.",
                data={
                    "status_code": response.status_code,
                    "response_text": response.text,
                },
            )
        except RequestException as exc:
            return DigiOperationResult(
                success=False,
                message=f"Failed to update system location: {exc}",
                data=None,
            )

    def reboot_device(
        self,
        device_id: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> DigiOperationResult:
        payload = f"""<sci_request version="1.0">
  <reboot>
    <targets>
      <device id="{device_id}"/>
    </targets>
  </reboot>
</sci_request>"""

        try:
            response = self._post_xml(
                self._settings.digi_sci_api,
                payload,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            return DigiOperationResult(
                success=True,
                message="Reboot command sent successfully.",
                data={
                    "status_code": response.status_code,
                    "response_text": response.text,
                },
            )
        except RequestException as exc:
            return DigiOperationResult(
                success=False,
                message=f"Failed to send reboot command: {exc}",
                data=None,
            )