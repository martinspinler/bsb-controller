import struct
import time

from . import types
from .types import Command, Flag
from .messages import messages, rows

from .locale.cs import message_text, addr_text

def swap_flags(t):
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
    def from_raw(cls, raw: bytes):
        if cls._crc(raw[0:-2]) != struct.unpack("!H", raw[-2:])[0]:
            raise CrcError

        sof, src, dst, length, cmd = raw[:5]
        param = struct.unpack("!I", raw[5:9])[0]
        param = swap_flags(param) if cmd in [Command.QUR, Command.SET] else param
        data = raw[9:-2]

        #assert sof == cls.SOF
        #assert cmd in set(Command)
        #assert length == len(raw)

        self = cls(param, data, cmd, dst, src & 0x7F)
        return self

    def to_raw(self) -> bytes:
        flags = bytes()
        length = 5 + 4 + len(self._data) + 2

        if Flag.FB in self._intflags:
            length += len(self._flags)
            flags = self._flags

        param = swap_flags(self._param) if self._cmd in [Command.QUR, Command.SET] else self._param

        raw  = bytes([self.SOF, self._src | 0x80, self._dst, length, self._cmd])
        raw += struct.pack("!I", param)
        raw += flags
        raw += self._data
        raw += struct.pack("!H", self._crc(raw))
        assert length == len(raw)
        return raw

    def __init__(self, param: int, data = bytes(), cmd: Command = Command.QUR, dst: int = DEF_DST, src: int = DEF_SRC):
        self._time = time.ctime()[4:-5]
        self._param = param
        self._data = data
        self._cmd = cmd
        self._dst = dst
        self._src = src
        self._value = None
        self._flags = bytes()

        msg_default = (Flag.NONE, None, "unknown")
        msg = messages.get(self._param, msg_default)
        if True and msg == msg_default:
            # Try just with row number only (ignore various flags)
            msg = messages.get(rows.get(self._param & 0xFFFF, None), msg_default)

        self._intflags, self._datatype, self._name = msg
        self.__update_data()

    def set_value(self, value):
        try:
            self._data = bytes(self._datatype.set(value))
            self.__update_data()

            #print("SV", list(self._data), self._flags, self._intflags)
        except Exception as e:
            print("Telegram: set_value error:", e, self)
            return False
        return True

    def __update_data(self):
        if self._intflags & Flag.FB and self._data:
            self._flags = self._data[:1]
            self._data = self._data[1:]
        elif self._intflags & Flag.LB and self._data:
            self._flags = self._data[-1:]
            self._data = self._data[:-1]

        if self._datatype and self._data:
            try:
                #print("UD", self._cmd, self._data, self._datatype)
                self._value = self._datatype.get(self)
            except Exception as e:
                print("Telegram: get_value error:", e, self)

    def __str__(self):
        src = addr_text.get(self._src, f"{self._src:02X}")
        dst = addr_text.get(self._dst, f"{self._dst:02X}")

        cmd = Command(self.cmd).name if self.cmd in set(Command) else 'UNK'
        text = self._name
        #text = message_text.get(self._name, self._name)
        value = self._value if self._value != None else ""

        base = f"{self._time} {src:<2}=>{dst:>2} {cmd} 0x{self._param:08x} {text:<30} {value:<20}"
        data = " ".join("{:02x}".format(x) for x in list(self._data)) # + "\n" + str(list(self.to_raw()))
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

    @property
    def datatype(self):
        return self._datatype

    @property
    def data(self):
        return self._data

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value
