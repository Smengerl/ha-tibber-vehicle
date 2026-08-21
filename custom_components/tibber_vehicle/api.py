"""Minimal Tibber Data API client for the Tibber Vehicle integration.

Deliberately thin — only the three GET endpoints this integration needs
(homes, devices, device detail). Response envelope shapes
(`{"homes": [...]}`, `{"devices": [...]}`, bare device-detail dict) are
taken from weconnect_mvp's tibber_client.py, confirmed live against the
real API on 2026-08-21 — see docs/CONTEXT.md §3. Auth (bearer token) is
supplied by the caller via `access_token_provider` rather than handled
here — this client never sees the OAuth2 flow itself, matching how
Spotify's `spotifyaio.SpotifyClient.refresh_token_function` keeps API
access and token refresh as separate concerns (see docs/DECISIONS.md).
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import ClientSession

from .const import API_BASE, USER_AGENT


class TibberVehicleApiError(Exception):
    """Raised when the Tibber Data API returns an unexpected response."""


class TibberVehicleApiClient:
    """Thin async wrapper around the Tibber Data API endpoints this integration needs."""

    def __init__(
        self,
        session: ClientSession,
        access_token_provider: Callable[[], Awaitable[str]],
    ) -> None:
        self._session = session
        self._access_token_provider = access_token_provider

    async def _get(self, path: str) -> dict[str, Any]:
        token = await self._access_token_provider()
        async with self._session.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
        ) as response:
            if response.status != 200:
                body = await response.text()
                raise TibberVehicleApiError(
                    f"Tibber API request to {path} failed: {response.status} {body}"
                )
            return await response.json()

    async def async_get_homes(self) -> list[dict[str, Any]]:
        """GET /homes — the customer's homes."""
        data = await self._get("/homes")
        return data.get("homes", [])

    async def async_get_devices(self, home_id: str) -> list[dict[str, Any]]:
        """GET /homes/{homeId}/devices — devices in a home."""
        data = await self._get(f"/homes/{home_id}/devices")
        return data.get("devices", [])

    async def async_get_device(self, home_id: str, device_id: str) -> dict[str, Any]:
        """GET /homes/{homeId}/devices/{deviceId} — full device state."""
        return await self._get(f"/homes/{home_id}/devices/{device_id}")

    async def async_find_first_vehicle(self) -> tuple[str, dict[str, Any]] | None:
        """Return (home_id, device) for the first device found, or None.

        With only the `data-api-vehicles-read` scope granted (this
        integration never requests chargers/thermostats/etc.), the devices
        endpoint returns vehicles only — confirmed live, see
        weconnect_mvp's tibber_client.py `vehicles()` docstring — so no
        extra category filtering is needed here. Multiple vehicles across
        multiple homes aren't handled yet (first one wins) — see
        docs/DECISIONS.md's known limitations.
        """
        for home in await self.async_get_homes():
            devices = await self.async_get_devices(home["id"])
            if devices:
                return home["id"], devices[0]
        return None
