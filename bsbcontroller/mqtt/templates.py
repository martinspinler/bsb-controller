from typing import Any
from dataclasses import dataclass


@dataclass
class Template:
    payload: dict[str, Any]
    component: str = "sensor"


def prec(x: int) -> dict[str, int]:
    return {
        "sug_dsp_prc": x
    }


device = {
    "identifiers": ["boiler"],
    "name": "Boiler",
    "model": "Nuvola Platinum+ 24",
    "manufacturer": "Baxi",
}

base = {
    "stat_t": "~/state",
    "platform": "mqtt",
    "device": device,
    "schema": "json",
}

temp = base | {
    "unit_of_measurement": "\xb0C",
    "device_class": "temperature",
}

meas = temp | prec(2) | {
    "state_class": "measurement",
}

power_factor = {
    "device_class": "power_factor",
    "unit_of_measurement": "%",
}

total_increasing = prec(0) | {
    "state_class": "total_increasing",
}

energy = {
    "device_class": "energy",
    "unit_of_measurement": "kWh",
}

pressure = prec(1) | {
    "device_class": "pressure",
    "unit_of_measurement": "bar",
}

req = {
    "cmd_t": "~/set",
}

req_temp = prec(2) | req | {
    "min": 18,
    "max": 25,
    "step": 0.5,
}

switch = {
    "payload_on": "true",
    "payload_off": "false",
    "state_on": True,
    "state_off": False,
}

button = {
    "payload_press": "true",
}
