#!/usr/bin/env python3
import time
import datetime
import logging

from functools import partial
from typing import Any

from . import Bsb

from .telegram import Telegram, Command, Message

from .http.logger import ThreadHttpLogServer, MyLogger
from .mqtt import MqttBsbClient


logger = logging.getLogger("HAC")
logging.basicConfig(level=logging.INFO)

client_ip, client_port = "127.0.0.1", 1883
bsb_port = "/dev/ttyAMA3"


def corr_none2zero(v):
    return 0 if v is None else v


corrections = {
    "pump_modulation_pct": corr_none2zero,
    "burner_modulation_pct": corr_none2zero,
}


def bsb_onetime_init(bsb: Bsb) -> None:
    bsb.set_value("datetime", datetime.datetime.now())

    #bsb.set_value("hc2_enabled", False)
    #bsb.set_value("hot_water_push", True)
    #bsb.set_value('room1_req_comfort_temp', 20.0)
    #bsb.set_value("room2_temp_status", 25.0, cmd=Command.INF)
    #bsb.set_value('hc1_operating_mode', 'reduced')
    #bsb.set_value('hc2_enabled', False)
    #bsb.set_value('hc2_operating_level', 'comfort')
    #bsb.set_value("room2_temp_status", 18.25)

    #bsb.get_value("hc1_status_qa")
    #bsb.get_value("status_msg2_qa")
    #bsb.get_value("hc1_time_prog_mon")

    #bsb.set_value('room1_req_comfort_temp', 20.0)
    #bsb.set_value('hc1_operating_mode', 'automatic')
    #bsb.set_value('hot_water_operating_mode', True)

    #days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    #for i in days[0:5]: bsb.set_value(f'hc1_time_prog_{i}', '5:00-6:30 16:00-22:00')
    #for i in days[5:7]: bsb.set_value(f'hc1_time_prog_{i}', '6:30-22:00')

    #for i in days[0:5]: bsb.set_value(f'hot_water_time_prog_{i}', '5:20-6:30 16:00-22:30')
    #for i in days[5:7]: bsb.set_value(f'hot_water_time_prog_{i}', '6:30-8:30 11:00-13:00 16:00-22:00')

    #bsb.set_value("hc1_time_prog_mon", "05:00-06:30 16:00-22:00")
    #bsb.get_value('hc1_time_prog_mon')


class MyBsbHandler():
    react = {
        "hc1_status": "room1_temp_req",
        "hc2_status": "room2_temp_req",
    }
    ignored = [
        Command.QUR,
    ]

    def __init__(self, bsb: Bsb) -> None:
        def sag(bsb: Bsb, req: str) -> None: # sleep and get
            time.sleep(2)
            bsb.get_value(req)

        self._bsb = bsb
        self._react = {k: partial(sag, bsb, v) for k, v in self.react.items()}

    def bsb_log_handler(self, telegram: Telegram) -> None:
        if telegram.cmd not in self.ignored:
            logger.info(str(telegram))

        if telegram.name in self._react:
            # The program can have changed the requested temperature
            self._react[telegram.name]()


def run(config: Any, monitored_msgs: dict[Message, int | None]) -> None:
    bsb = Bsb(config.get("bsbport"))
    bsb.set_monitored(monitored_msgs)

    bsb.loggers.append(MyBsbHandler(bsb).bsb_log_handler)
    log = ThreadHttpLogServer(MyLogger(bsb))

    bsb.start()

    bsb_onetime_init(bsb)
    if config.get("mqtt") is not None:
        mc = MqttBsbClient(bsb, config.get("mqtt"))
        mc.corrections.update(corrections)
        mc.start()

    try:
        while True:
            time.sleep(10**8)
    finally:
        if mc is not None:
            mc.stop()
        log.server.shutdown()
        bsb.stop()
