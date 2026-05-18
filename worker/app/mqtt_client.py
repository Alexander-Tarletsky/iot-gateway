import logging
from datetime import datetime, timezone
from queue import Queue
from typing import NamedTuple, Optional

import paho.mqtt.client as mqtt

from app.config import Config

logger = logging.getLogger(__name__)


class MqttMessage(NamedTuple):
    topic: str
    payload: bytes
    received_at: datetime


class MqttSubscriber:
    def __init__(self, config: Config, message_queue: Queue[MqttMessage]) -> None:
        self._config = config
        self._queue = message_queue
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.mqtt_client_id,
        )
        if config.mqtt_username:
            self._client.username_pw_set(config.mqtt_username, config.mqtt_password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def start(self) -> None:
        logger.info(
            "Connecting to MQTT broker at %s:%s",
            self._config.mqtt_host,
            self._config.mqtt_port,
        )
        self._client.connect(
            self._config.mqtt_host,
            self._config.mqtt_port,
            keepalive=60,
        )
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("MQTT client stopped")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        connect_flags: object,
        reason_code: mqtt.ReasonCode,
        properties: Optional[object] = None,
    ) -> None:
        if reason_code.is_failure:
            logger.error("MQTT connect failed: %s", reason_code)
            return
        logger.info("MQTT connected, subscribing to %s", self._config.mqtt_topic)
        client.subscribe(self._config.mqtt_topic, qos=1)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: object,
        msg: mqtt.MQTTMessage,
    ) -> None:
        received_at = datetime.now(timezone.utc)
        self._queue.put(
            MqttMessage(topic=msg.topic, payload=msg.payload, received_at=received_at)
        )

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: object,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: Optional[object] = None,
    ) -> None:
        if reason_code.is_failure:
            logger.warning("MQTT disconnected unexpectedly: %s", reason_code)
        else:
            logger.info("MQTT disconnected: %s", reason_code)
