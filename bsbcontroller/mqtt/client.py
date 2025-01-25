import time
import threading
import json
from typing import Callable, Any

import paho.mqtt.client as mqtt_client

from .. import Bsb
from ..telegram import Telegram, Command
from .templates import Template
from . import messages


class MqttBsbClient(threading.Thread):
    items = messages.boiler_requests
    enabled_requests: list[str]
    translationss: dict[str, str]
    corrections: dict[str, Callable[[Any], Any]] = {}

    def __init__(self, bsb: Bsb, config: Any):
        threading.Thread.__init__(self)

        client = self._client = mqtt_client.Client(client_id="bsb")

        client.on_connect = self._on_connect
        client.on_message = self._on_message

        self._bsb = bsb

        self._values: dict[str, Any] = {}
        self._prefix = "home/boiler"
        self._enabled_topics: list[str] = []

        self._config = config
        self.translations = self._config.get("rename", {})
        self.enabled_requests = self._config.get("allow_set", [])

    def start(self) -> None:
        while True:
            try:
                addr = self._config.get("addr", "127.0.0.1")
                port = self._config.get("port", 1883)
                self._client.connect(addr, port, 60)
            except ConnectionRefusedError:
                time.sleep(5)
                continue
            else:
                break

        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client: mqtt_client.Client, userdata: Any, flags: dict[str, Any], rc: Any) -> None:
        self._client.subscribe("#")

        self._bsb.callbacks.append(self._bsb_callback)
        self._bsb.loggers.append(self._bsb_log)

        self.setup_mqtt_ha_discovery()
        for name in self.items.keys():
            self._bsb.get_value(name)

    def _on_message(self, client: mqtt_client.Client, userdata: Any, msg: mqtt_client.MQTTMessage) -> None:
        topic = msg.topic

        if topic.startswith(f"{self._prefix}/") and topic.endswith("/set"):
            request = topic.removeprefix(f"{self._prefix}/").removesuffix("/set")
            request = self.translations.get(request, request)

            if request in self.enabled_requests:
                val = msg.payload.decode()
                try:
                    val = json.loads(val)
                except Exception:
                    pass

                self._bsb.set_value(request, val)

    def _bsb_callback(self, request: str, value: Any) -> None:
        if request in self._enabled_topics:
            added = False
            if request not in self._values:
                self._values[request] = None
                added = True

            if request in self.corrections:
                value = self.corrections[request](value)

            if value != self._values[request] or added:
                self._values[request] = value

                name = self.translations.get(request, request)
                self._client.publish(f"{self._prefix}/{name}/state", value, retain=True)

    def _bsb_log(self, telegram: Telegram) -> None:
        if telegram.cmd in [Command.INF]:
            self._bsb_callback(telegram.name, telegram.value)
        elif telegram.cmd == Command.ANS and telegram.dst != Telegram.DEF_SRC:
            self._bsb_callback(telegram.name, telegram.value)

    def _publish_config(self, request: str, template: Template) -> None:
        component = template.component
        name = self.translations.get(request, request)
        payload = template.payload | {
            "~": f"{self._prefix}/{name}",
            "name": name,
            "uniq_id": name,
        }

        topic = f"homeassistant/{component}/boiler/{name}/config"
        self._client.publish(topic=topic, payload=json.dumps(payload), qos=0, retain=True)
        self._enabled_topics.append(request)

    def setup_mqtt_ha_discovery(self) -> None:
        for name, template in self.items.items():
            self._publish_config(name, template)
