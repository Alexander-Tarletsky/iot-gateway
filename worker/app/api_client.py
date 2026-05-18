import json
import logging
import time

import requests

from app.config import Config
from app.mqtt_client import MqttMessage

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

        body = {
            "topic": message.topic,
            "received_at": message.received_at.isoformat(),
            **sensor_data,
        }

        return self._post_with_retries(body)

    def _post_with_retries(self, body: dict) -> bool:
        attempts = self._config.http_retry_count + 1
        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(
                    self._config.api_url,
                    json=body,
                    timeout=self._config.http_timeout_sec,
                )
                if response.ok:
                    logger.info(
                        "Forwarded to %s (status %s)",
                        self._config.api_url,
                        response.status_code,
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
