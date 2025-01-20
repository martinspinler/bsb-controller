import struct
import datetime
import logging
import traceback

from typing import Any
from .types import Command, Flag
from .messages import messages, rows


logger = logging.getLogger("BSB")

addr_text = {
    0x00: "K", # Boiler
    0x06: "T", # 1. thermostat
    0x07: "U", # 2. thermostat
    0x08: "V", # 3. thermostat
    0x7f: "B", # Broadcast
    0x42: "L", # LAN controller
}


def swap_flags(t: int) -> int:
    return ((t & 0x00ff0000) << 8) | ((t & 0xff000000) >> 8) | (t & 0xffff)


class CrcError(Exception):
    pass


class Telegram(object):
    SOF = 0xDC
    DEF_SRC = 0x42
    DEF_DST = 0x00

    @staticmethod
    def _crc(raw: bytes) -> int:
        crcval = 0
        for byte in raw:
            crcval = (crcval ^ (byte << 8)) & 0xffff
            for bit in range(8):
                if crcval & 0x8000:
                    crcval = (crcval << 1) ^ 0x1021
                else:
                    crcval <<= 1
                crcval &= 0xffff
        return crcval

    @classmethod
    def from_raw(cls, raw: bytes, timestamp: datetime.datetime | None = None) -> "Telegram":
        if cls._crc(raw[0:-2]) != struct.unpack("!H", raw[-2:])[0]:
            raise CrcError

        sof, src, dst, length, cmd = raw[:5]
        param = struct.unpack("!I", raw[5:9])[0]
        cmd = Command(cmd)
        param = swap_flags(param) if cmd in [Command.QUR, Command.SET] else param
        rawdata = raw[9:-2]

        #assert sof == cls.SOF
        #assert cmd in set(Command)
        #assert length == len(raw)

        self = cls(param, rawdata, cmd, dst, src & 0x7F, timestamp, override=False)
        return self

    def to_raw(self) -> bytes:
        param = swap_flags(self._param) if self._cmd in [Command.QUR, Command.SET] else self._param

        raw = bytearray([self.SOF, self._src | 0x80, self._dst, 0x0, self._cmd])
        raw += struct.pack("!I", param)
        raw += self._rawdata
        raw[3] = len(raw) + 2
        raw += struct.pack("!H", self._crc(raw))
        return bytes(raw)

    def __init__(self, param: int, rawdata: bytes = bytes(), cmd: Command = Command.QUR, dst: int = DEF_DST, src: int = DEF_SRC, timestamp: datetime.datetime | None = None, override: bool = True):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        #self._time = timestamp.ctime()[4:-5]
        self._time = timestamp.strftime("%d.%m. %H:%M:%S")
        self._param = param
        self._rawdata = rawdata
        self._cmd = cmd
        self._dst = dst
        self._src = src
        self._value: Any = None
        self._flags = bytes()
        self._index = None

        msg_default = (Flag.FB, None, "unknown")
        msg = messages.get(self._param, msg_default)
        if False and msg == msg_default:
            # Try just with row number only (ignore various flags)
            msg = messages.get(rows.get(self._param & 0xFFFF, None), msg_default)

        if False: # is_indexed?
            self._index = (self.param >> 24) & 0x3

        self._intflags: Flag
        self._intflags, self._datatype, self._name = msg

        if override:
            if self._intflags & Flag.BC:
                self._dst = 0x7F

            # Override SET to INF
            if self._intflags & Flag.IF and self._cmd == Command.SET:
                self._cmd = Command.INF

            if self._intflags & Flag.QI and self._cmd == Command.QUR:
                self._cmd = Command.QIN

        # HOTFIX for stored data
        if not override and self._param in [0x3d2d0215] and len(self._rawdata) == 2:
            self._rawdata += b"\xbe"

        self._rawdata2data()
        self._update_value()

    def set_value(self, value: Any) -> bool:
        try:
            if self._datatype is None:
                raise Exception("Can't set telegram with no value type")
            self._data = self._datatype.enc(value)

            if self._intflags & Flag.FB:
                #assert self.cmd == Command.SET
                self._flags = bytes([0]) if value is None else bytes([1])

            if self._intflags & Flag.LB:
                #assert self.cmd == Command.INF
                self._flags = bytes([0]) # TODO: Check this

            self._update_value()
            self._data2rawdata()

        except Exception as e:
            logger.error(f"Telegram.set_value error: {e}, {self}")
            logger.error(traceback.format_exc())
            return False
        return True

    def _rawdata2data(self) -> None:
        rd = list(self._rawdata)
        f, d = [], rd

        if rd:
            if self.cmd in [Command.NAK, Command.ERR]:
                f, d = rd[:1], rd[1:]
            if self._intflags & Flag.FB:
                f, d = rd[:1], rd[1:]
            elif self._intflags & Flag.LB and self.cmd in [Command.INF]:
                f, d = rd[-1:], rd[:-1]
        self._flags, self._data = bytes(f), d

    def _data2rawdata(self) -> None:
        rd = bytes()
        if Flag.FB in self._intflags:
            rd += self._flags
        rd += bytes(self._data)
        if Flag.LB in self._intflags:
            rd += self._flags
        self._rawdata = rd

    def _update_value(self) -> None:
        if self._data and self._datatype is not None:
            try:
                self._value = self._datatype.dec(self.data)
                nullable = False
                nullable |= bool(self._intflags & Flag.FB) and self.cmd in [Command.ANS, Command.SET]
                #nullable |= bool(self._intflags & Flag.LB) and self.cmd in [Command.INF]
                if nullable:
                    assert len(self._flags) == 1
                    if (self._flags[0] == 0x01 and self.cmd == Command.ANS):  # TODO: Command.SET ?
                        self._value = None
            except Exception as e:
                logger.error(f"Telegram.get_value error: {e}, {self}")
                logger.error(f"Intflags: {self._intflags}, rawdata: {list(self._rawdata)}")
                logger.error(traceback.format_exc())

    def __str__(self) -> str:
        src = addr_text.get(self._src, f"{self._src:02X}")
        dst = addr_text.get(self._dst, f"{self._dst:02X}")

        cmd = Command(self.cmd).name if self.cmd in set(Command) else 'UNK'
        text = self._name
        #text = message_text.get(self._name, self._name)
        value = str(self._value) if self._value is not None else ""

        base = f"{self._time} {src:<2}=>{dst:>2} {cmd} 0x{self._param:08x} {text:<25.25} {value:<20}"
        data = " ".join("{:02x}".format(x) for x in self._data)
        if self._intflags & Flag.FB and self._flags:
            data = f"|{self._flags[0]:02x}|{data}|"
        elif self._intflags & Flag.LB and self._flags:
            data = f"   |{data}|{self._flags[0]:02x}"
        elif data:
            data = f"   |{data}|"
        return f"{base} {data}"

    @property
    def src(self) -> int:
        return self._src

    @property
    def dst(self) -> int:
        return self._dst

    @property
    def cmd(self) -> Command:
        return self._cmd

    @property
    def param(self) -> int:
        return self._param

    #@property
    #def datatype(self):
    #    return self._datatype

    @property
    def data(self) -> list[int]:
        return self._data

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Any:
        return self._value
