"""
alert_pusher.py — Secure push of incident alerts to the central command backend

Auth: X-Service-Token header (same pattern as vehicle-tracking/events.py).
      The backend's verify_service_token() uses constant-time comparison.

Post-hackathon: add HMAC-SHA256 signature (X-Signature-SHA256) alongside the
service token for production deployment — prevents request replay from
compromised bus units.

Retry logic: failed pushes go into a bounded deque (max 50). flush_queue()
should be called from the main loop every few seconds. Alerts are never
silently dropped.
"""

import json
import time
from collections import deque
from typing import Optional

import requests

from config import BACKEND_URL, SEND_TO_BACKEND, SERVICE_TOKEN

_MAX_QUEUE  = 50
_TIMEOUT_S  = 8


class AlertPusher:
    def __init__(self, api_url: str = BACKEND_URL):
        self._api_url     = api_url
        self._retry_queue: deque = deque(maxlen=_MAX_QUEUE)
        self._last_flush  = time.time()

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def push(self, payload: dict) -> bool:
        """
        POST the alert to the backend.

        Args:
            payload: the alert dict from alert_builder.build_alert()
                     (already has _meta stripped by strip_meta())

        Returns:
            True if the backend accepted it (2xx), False otherwise.
        """
        if not SEND_TO_BACKEND:
            self._log_local(payload)
            return True

        if not SERVICE_TOKEN:
            print("[AlertPusher] ⚠️  SERVICE_TOKEN not set — set $env:SERVICE_TOKEN")

        return self._do_post(payload)

    def flush_queue(self) -> None:
        """
        Retry any queued failed alerts.
        Safe to call every frame — internally throttles to once per 5 seconds.
        """
        now = time.time()
        if now - self._last_flush < 5.0:
            return
        self._last_flush = now

        retry_batch = list(self._retry_queue)
        self._retry_queue.clear()

        for queued_payload in retry_batch:
            if not self._do_post(queued_payload):
                # Still failing — put back
                self._retry_queue.append(queued_payload)

        if retry_batch:
            remaining = len(self._retry_queue)
            print(f"[AlertPusher] Retry flush: {len(retry_batch)} attempted, "
                  f"{remaining} still queued")

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _do_post(self, payload: dict) -> bool:
        headers = {
            "Content-Type":    "application/json",
            "X-Service-Token": SERVICE_TOKEN,
        }
        try:
            resp = requests.post(
                self._api_url,
                data=json.dumps(payload, default=str),
                headers=headers,
                timeout=_TIMEOUT_S,
            )
            if resp.status_code == 201:
                event_id = resp.json().get("id", "?")
                plate    = payload.get("plate_text", "—")
                print(f"[AlertPusher] ✅ 201 Created | event_id={event_id} | plate={plate}")
                return True
            else:
                print(f"[AlertPusher] ❌ HTTP {resp.status_code}: {resp.text[:200]}")
                self._retry_queue.append(payload)
                return False

        except requests.exceptions.Timeout:
            print(f"[AlertPusher] ⏱ Timeout — queued for retry "
                  f"(queue size: {len(self._retry_queue)+1})")
            self._retry_queue.append(payload)
            return False

        except requests.exceptions.RequestException as exc:
            print(f"[AlertPusher] ⚠️  Network error ({exc}) — queued for retry")
            self._retry_queue.append(payload)
            return False

    def _log_local(self, payload: dict) -> None:
        """Pretty-print alert when SEND_TO_BACKEND=False (dry-run mode)."""
        print("\n" + "═" * 60)
        print("📡 [DRY RUN] Alert would be sent:")
        print(json.dumps(payload, indent=2, default=str))
        print("═" * 60 + "\n")
