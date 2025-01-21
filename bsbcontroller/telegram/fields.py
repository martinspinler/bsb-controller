import abc
import inspect
import re
from typing import Type, Optional, Any, ClassVar
from struct import pack, unpack
from dataclasses import dataclass

import datetime


def clamp(n: int, smallest: int, largest: int) -> int:
    return max(smallest, min(n, largest))


class Field(abc.ABC):
    #In a ret telegram, flag 00 indicates a "normal" value, 01 a null value. In the latter case, the <value> byte should be ignored.
    #In a set telegram, the flag is set to:
    #01 when setting the value of a non-nullable field;
    #05 when setting a value for a nullable field;
    #06 when setting a nullable field to NULL (in this case, the <value> byte will be ignored).
    @classmethod
    def dec(cls, data: list[int]) -> Any:
        raise NotImplementedError(f"dec missing for {cls}")

    @classmethod
    def enc(cls, value: Any) -> list[int]:
        raise NotImplementedError(f"enc missing for {cls}")


class Temp(Field):
    @classmethod
    def dec(cls, data: list[int]) -> float:
        return int(unpack("!h", bytes(data[0:2]))[0]) / 64

    @classmethod
    def enc(cls, value: float | None) -> list[int]:
        return list(pack("!h", 0 if value is None else int(value * 64)))


class OnOff(Field):
    @classmethod
    def dec(cls, data: list[int]) -> bool:
        return data[0] > 0

    @classmethod
    def enc(cls, value: bool) -> list[int]:
        return [1 if value else 0]


class Enum(Field):
    values: dict[int, Any] = {}
    offset = 0
    unknown: str | Type[Exception] = "unknown"

    _values_rev = None

    @classmethod
    def dec(cls, data: list[int]) -> Any:
        ret = cls.values.get(data[cls.offset], cls.unknown)
        if inspect.isclass(ret) and issubclass(ret, Exception):
            raise ret
        return ret

    @classmethod
    def enc(cls, value: Any) -> list[int]:
        if cls._values_rev is None:
            cls._values_rev = dict((v, k) for k, v in cls.values.items())
        return [cls._values_rev[value]]


class Enable(Enum):
    unknown = Exception
    values: dict[int, bool] = {
        0xFF: True,
        0x00: False,
    }


class CStatus(Enum): # also for boiler_status
    values = {
        0x00: "disabled",
        0x10: "modulation", # for burner_state
        0x11: "finishing", # dobeh # overrun_active
        0x12: "in_operation",
        0x19: "off",
        0x4b: "charged", # Hot water status r.8009
        0x45: "charging_active",
        0x5d: "charging_forced", # vynucene nabijeni, zadana T
        0x60: "charging_to_req_temp", # Nabijeni, jmen. zadana teplota
        0x63: "nabito_jmenovita_teplota", # charged_nominal_temp
        0x68: "omezeno_prednost_hw",
        0x6e: "forced_circulation",
        0x72: "heat_comfort", # on_heating_mode! (Prelozeno jako Rezim vytapeni komfort)
        0x74: "heat_reduced", # reduced_heating_mode, Tlumeny provoz vytapeni
        0x78: "setback_reduced", # pokles redukovan
        0x7a: "room_temp_limitation",
        0xa6: "HC", # in operation for CH
        0xa7: "partial HC",
        0xa8: "hotwater", # TODO: CHECK
        0xa9: "hotwater2", # TODO: CHECK
        0xae: "finishing hotwater", # TODO: CHECK
        0xaf: "release HC",
        0xd8: "off_stby",
    }


class OpMode(Enum):
    values = {
        0: 'protection',
        1: 'automatic',
        2: "reduced",
        3: "comfort",
    }


class Int(Field):
    size: int
    char: str

    @classmethod
    def dec(cls, data: list[int]) -> int:
        return int(unpack(f"!{cls.char}", bytes(data[0:cls.size]))[0])

    @classmethod
    def enc(cls, data: int) -> list[int]:
        return list(pack(f"!{cls.char}", data))


class Int8(Int):
    size = 1
    char = 'B'


class Int16(Int):
    size = 2
    char = 'H'


class Int32(Int):
    size = 4
    char = 'L'


class Pct2(Field):
    @classmethod
    def dec(cls, data: list[int]) -> float:
        return int(unpack("!H", bytes(data[0:2]))[0]) / 100.0


class Date(Field):
    @classmethod
    def dec(cls, data: list[int]) -> str:
        _, Y, M, D, d, h, m, s, _ = data
        return f"{D:02}.{M:02}.{Y + 1900:02} {h:02}:{m:02}:{s:02}"

    @classmethod
    def enc(cls, value: Any) -> list[int]:
        v = value
        if isinstance(value, str):
            date_format = '%Y-%m-%d %H:%M:%S'
            v = datetime.datetime.strptime(value, date_format)

        if isinstance(v, datetime.datetime):
            return [0, v.year - 1900, v.month, v.day, (v.weekday() + 1) % 7, v.hour, v.minute, v.second, 0]

        return []


class Float10(Field):
    @classmethod
    def dec(cls, data: list[int]) -> float:
        return int(unpack("!H", bytes(data[0:2]))[0]) / 10.0

    @classmethod
    def enc(cls, data: float) -> list[int]:
        return list(pack("!H", int(data * 10)))


class Error(Field):
    @classmethod
    def dec(cls, data: list[int]) -> str:
        errno = data[1]
        if data == [0x7f, 0x06]:
            return f"{errno}: Legionelni teplota"
        if data == [0x69, 0x05]:
            return f"{errno}: Nizky tlak vody"
        return f"{errno}: Neznama chyba"


class HWater(Field):
    @classmethod
    def dec(cls, data: list[int]) -> str:
        s = ("charging" if data[1] & 0x08 else "ready")
        s += ("" if data[1] & 0x04 else ", stby") # Also status byte is 0 in stby mode?
        return s


class StatB(Field):
    @classmethod
    def dec(cls, data: list[int]) -> str:
        # data[3] == 0x59: enabled for HC1, 0x5B: enabled for HC2 + HC1
        return "Burner: {0}".format(2 if data[0] & 0x10 else (1 if data[0] & 0x04 else 0))


@dataclass
class Plan(Field):
    plan: list[Optional[tuple[datetime.time, datetime.time]]]

    def __str__(self) -> str:
        return " ".join(["{0}-{1}".format(p[0].strftime("%H:%M"), p[1].strftime("%H:%M")) if p is not None else "" for p in self.plan])

    @classmethod
    def dec(cls, data: list[int]) -> "Plan":
        plan: list[Optional[tuple[datetime.time, datetime.time]]] = []
        for i in [0, 2, 4]:
            if data[i] == 0xFF:
                plan.append(None)
            else:
                time1 = (datetime.datetime.fromtimestamp(0, datetime.UTC) + datetime.timedelta(minutes=(10 * data[i + 0]))).time()
                time2 = (datetime.datetime.fromtimestamp(0, datetime.UTC) + datetime.timedelta(minutes=(10 * data[i + 1]))).time()
                plan.append((time1, time2))
        return cls(plan)


@dataclass
class StatHW(Field):
    stby: bool
    outdoor_temp: float
    water_pressure: float
    plan: Plan

    def __str__(self) -> str:
        return f"OT: {self.outdoor_temp:5.1f}, WP: {self.water_pressure:.1f} Stby: {self.stby} Plan: {self.plan}"

    @classmethod
    def dec(cls, data: list[int]) -> "StatHW":
        return cls(
            bool(data[10] & 0x08),
            Temp.dec(data[0:2]),
            Float10.dec(data[2:4]),
            Plan.dec(data[4:10]),
        )


@dataclass
class HCStat(Field):
    mode: str
    current: str
    plan: Plan
    running: bool

    current_values: ClassVar[dict[int, str]] = {
        0: 'protection',
        1: 'reduced',
        2: 'comfort',
    }

    def __str__(self) -> str:
        return f"mode: {self.mode} cur: {self.current} run: {self.running} plan: {self.plan}"

    @classmethod
    def dec(cls, data: list[int]) -> "HCStat":
        return cls(
            OpMode.dec(data[0:1]),                    # Currently selected mode
            HCStat.current_values.get(data[1], 'unknown'), # Mode applied by schedule
            Plan.dec(data[2:8]),
            data[8] == 0x02                             # Boiler is running (for some HC)?
        )
        # TODO: Check
        #unknown2 = data[9]


class Schedule(Field):
    @classmethod
    def dec(cls, data: list[int]) -> str:
        groups = [data[(i * 4):(i * 4 + 4)] for i in range(3)]
        return " ".join(["{0:02}:{1:02}-{2:02}:{3:02}".format(*time[0:4]) for time in groups if not (time[0] & 0x80)])

    @classmethod
    def enc(cls, value: Any) -> list[int]:
        ret = []
        match = re.findall(r'(\d+):(\d+)-(\d+):(\d+)', value)
        if not match:
            raise Exception("Can't parse time from schedule")
        for i in range(3):
            if len(match) > i:
                h1, m1, h2, m2 = [int(x) for x in match[i]]
                if clamp(h1, 0, 23) != h1 or clamp(h2, 0, 23) != h2 or clamp(m1, 0, 59) != m1 or clamp(m2, 0, 59) != m2:
                    raise Exception("Can't parse time from schedule")
                if h1 * 60 + m1 > h2 * 60 + m2:
                    raise Exception("Can't parse time from schedule")
                ret += [h1, m1, h2, m2]
            else:
                ret += [0x80, 0, 0, 0]
        return ret
