"""Minimal Tibber Data API client for the Tibber Vehicle integration.

Deliberately thin — only the three GET endpoints this integration needs
(homes, devices, device detail). Response envelope shapes
(`{"homes": [...]}`, `{"devices": [...]}`, bare device-detail dict) were
confirmed live against the real API on 2026-08-21 — see docs/CONTEXT.md
§3. Auth (bearer token) is
supplied by the caller via `access_token_provider` rather than handled
here — this client never sees the OAuth2 flow itself, matching how
Spotify's `spotifyaio.SpotifyClient.refresh_token_function` keeps API
access and token refresh as separate concerns (see docs/DECISIONS.md).

Retries with exponential backoff + full jitter on 429/5xx, per Tibber's
own documented guidance (docs/CONTEXT.md §3) — never on 400/401/403/404,
which mean "fix the request", not "try again".
"""
from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from .const import API_BASE, USER_AGENT

REQUEST_TIMEOUT = ClientTimeout(total=30)
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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
        headers = {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}

        for attempt in range(MAX_RETRIES + 1):
            async with self._session.get(
                f"{API_BASE}{path}", headers=headers, timeout=REQUEST_TIMEOUT
            ) as response:
                if response.status == 200:
                    return await response.json()

                if response.status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                    backoff = BASE_BACKOFF_SECONDS * (2**attempt)
                    await asyncio.sleep(random.uniform(0, backoff))
                    continue

                body = await response.text()
                raise TibberVehicleApiError(
                    f"Tibber API request to {path} failed: {response.status} {body}"
                )

        raise TibberVehicleApiError(
            f"Tibber API request to {path} failed after {MAX_RETRIES} retries"
        )

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

    async def async_get_all_vehicles(self) -> list[tuple[str, dict[str, Any]]]:
        """Return (home_id, device) for every vehicle across all homes.

        Vehicles are "ambulatory" and appear under every home the token can
        see (confirmed live, see docs/CONTEXT.md §3), so de-duplication by
        device id is required to avoid counting the same vehicle once per
        home. With only the `data-api-vehicles-read` scope granted (this
        integration never requests chargers/thermostats/etc.), the devices
        endpoint returns vehicles only — confirmed live (see
        docs/CONTEXT.md §3) — so no extra category filtering is needed here.
        """
        seen: set[str] = set()
        result: list[tuple[str, dict[str, Any]]] = []
        for home in await self.async_get_homes():
            for device in await self.async_get_devices(home["id"]):
                device_id = device.get("id")
                if device_id and device_id not in seen:
                    seen.add(device_id)
                    result.append((home["id"], device))
        return result
