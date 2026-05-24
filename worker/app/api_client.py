import json
import logging
import time
from typing import Any, Dict, Optional

import requests

from app.config import Config
from app.mqtt_client import MqttMessage
from app.odoo_datetime import parse_device_timestamp, to_odoo_datetime

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, config: Config) -> None:
        self._config = config

    def forward(self, message: MqttMessage) -> bool:
        try:
            sensor_data = json.loads(message.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error(
                "Invalid JSON payload on topic %s: %s",
                message.topic,
                exc,
            )
            return False

        if not isinstance(sensor_data, dict):
            logger.error("Expected JSON object on topic %s", message.topic)
            return False

        body = self._build_odoo_payload(sensor_data, message)
        if body is None:
            return False

        return self._post_with_retries(body)

    def _build_odoo_payload(
        self, sensor_data: Dict[str, Any], message: MqttMessage
    ) -> Optional[Dict[str, Any]]:
        if "temperature" not in sensor_data or "humidity" not in sensor_data:
            logger.error(
                "Missing temperature or humidity on topic %s: %s",
                message.topic,
                list(sensor_data.keys()),
            )
            return None

        try:
            temperature = float(sensor_data["temperature"])
            humidity = float(sensor_data["humidity"])
        except (TypeError, ValueError) as exc:
            logger.error("Invalid temperature/humidity on topic %s: %s", message.topic, exc)
            return None

        device_id = sensor_data.get("device_id") or self._config.device_id

        payload: Dict[str, Any] = {
            "device_id": str(device_id),
            "temperature": temperature,
            "humidity": humidity,
        }

        raw_timestamp = sensor_data.get("timestamp") or sensor_data.get("reading_time")
        if raw_timestamp is not None:
            try:
                payload["timestamp"] = to_odoo_datetime(
                    parse_device_timestamp(raw_timestamp)
                )
            except (ValueError, TypeError) as exc:
                logger.error(
                    "Invalid timestamp on topic %s: %s",
                    message.topic,
                    exc,
                )
                return None
        else:
            payload["timestamp"] = to_odoo_datetime(message.received_at)

        return payload

    def _request_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Climate-Api-Key": self._config.climate_api_key,
        }

    def _post_with_retries(self, body: Dict[str, Any]) -> bool:
        attempts = self._config.http_retry_count + 1
        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(
                    self._config.api_url,
                    json=body,
                    headers=self._request_headers(),
                    timeout=self._config.http_timeout_sec,
                )
                if response.ok:
                    record_id = None
                    try:
                        data = response.json()
                        record_id = data.get("id")
                    except ValueError:
                        pass
                    logger.info(
                        "Forwarded to %s (status %s%s)",
                        self._config.api_url,
                        response.status_code,
                        f", id={record_id}" if record_id is not None else "",
                    )
                    return True
                logger.warning(
                    "API returned %s on attempt %s/%s: %s",
                    response.status_code,
                    attempt,
                    attempts,
                    response.text[:200],
                )
            except requests.RequestException as exc:
                logger.warning(
                    "API request failed on attempt %s/%s: %s",
                    attempt,
                    attempts,
                    exc,
                )

            if attempt < attempts:
                time.sleep(self._config.http_retry_delay_sec)

        return False
