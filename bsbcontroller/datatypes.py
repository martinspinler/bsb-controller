from struct import pack, unpack
import datetime
from .types import Command


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

def get_temp(data):
    return unpack("!h", data)[0] / 64

def get_float_decimal(data):
    return data[0] / 10.0


class TT(object):
    #In a ret telegram, flag 00 indicates a "normal" value, 01 a null value. In the latter case, the <value> byte should be ignored.
    #In a set telegram, the flag is set to:
    #01 when setting the value of a non-nullable field;
    #05 when setting a value for a nullable field;
    #06 when setting a nullable field to NULL (in this case, the <value> byte will be ignored).
    def get(t):
        pass
    def set(t, v):
        return None


class TTTemp(TT):
    def get(t):
        if t.cmd == Command.ANS and t.data[0] == 1:
            return None

        return get_temp(t.data[0:2])

    def set(t, v):
        if v == None:
            return [1, 0, 0]
        v = int(v * 64)
        return [1, v // 256, v % 256]

class TTOnOff(TT):
    def get(t):
        return True if t.data[0] > 0 else False

    def set(t, v):
        return [1, 1 if v else 0]

class TTHCStatus(TT):
    def get(t):
        manual_set = bool(t.data[1] & 0x02)
        running = bool(t.data[8] & 0x02)
        hc_mode = TTOpLvl.values[t.data[0]] if t.data[0] in TTOpLvl.values else 'unknown'
        return ""

class TTSchedule(TT):
    def get(t):
        text = []
        for i in range(3):
            time = t.data[i*4:i*4+4]
            if not (time[0] & 0x80):
                text += ["{0:02}:{1:02}-{2:02}:{3:02}".format(*time[0:4])]
        return " ".join(text)

    def set(t, v):
        ret = []
        l = re.findall(r'(\d+):(\d+)-(\d+):(\d+)', v)
        if not l:
            return None
        for i in range(3):
            if len(l) > i:
                h1, m1, h2, m2 = [int(x) for x in l[i]]
                if clamp(h1, 0, 23) != h1 or clamp(h2, 0, 23) != h2 or clamp(m1, 0, 59) != m1 or clamp(m2, 0, 59) != m2:
                    return None
                if h1 * 60 + m1 > h2 * 60 + m2:
                    return None
                ret += [h1, m1, h2, m2]
            else:
                ret += [0x80, 0, 0, 0]
        return ret
            

        # {4:02}:{5:02}-{6:02}:{7:02} {8:02}:{9:02}-{10:02}:{11:02}".format(*t)
    #Schedule fields encode up to three time intervals for 1 day. They like to come in bunches of 7 (meaning monday..sunday).
    #They have 12 bytes: hh1 mm1 hh2 mm2 ... hh6 mm6. The active intervals are then hh1:mm1-hh2:mm2, hh3:mm3-hh4:mm4, hh5:mm5-hh6:mm6.
    #Unused intervals are set by the sequence 80 00 00 00. (My device then returns 98 00 18 00 when getting the value.)
    #The LCD panel sorts unused intervals to the end, sorts by start time and merges overlapping intervals.#


class TTPct(TT):
    def get(t):
        return t.data[0]

class TTBStatus(TT):
    def get(t):
        val = unpack("!h", t.data)[0]
        sel = {
            0x00a6: "HC",
            0x0011: "finishing",
            0x0019: "off",
        }
        return sel[val] if val in sel else "unknown"

class TTBHCMode(TT):
    def get(t):
        val = unpack("!h", t.data)[0]
        sel = {
            0x0072: "heat_comfort",
            0x006e: "forced_circulation",
            0x0019: "off",
        }
        return sel[val] if val in sel else "unknown"

class TTPct2(TT):
    def get(t):
        return unpack("!H", t.data[0:2])[0] / 100.0

class TTOpLvl(TT):
    values = {0: 'protection', 1: 'automatic', 2: "reduced", 3: "comfort"}
    def get(t):
        return TTOpLvl.values[t.data[0]] if t.data[0] in TTOpLvl.values else 'unknown'

    def set(t, v):
        d = dict((v, k) for k,v in TTOpLvl.values.items())
        return [1, d[v]] if v in d else None

class TTDate(TT):
    def get(t):
        Y, M, D, d, h, m, s = t.data[1:8]
        return f"{D:02}.{M:02}.{Y+1900:02} {h:02}:{m:02}:{s:02}"

    def set(t, v):
        if isinstance(v, str):
            #v = '2023-02-28 14:30:00'
            date_format = '%Y-%m-%d %H:%M:%S'
            v = datetime.datetime.strptime(v, date_format)

        if isinstance(v, datetime.datetime):
            return [0, v.year - 1900, v.month, v.day, (v.weekday() + 1 ) % 7, v.hour, v.minute, v.second, 0]

        return []

class TTInt32(TT):
    def get(t):
        return unpack("!I", t.data[0:4])[0]

class TTInt16(TT):
    def get(t):
        return unpack("!H", t.data[0:2])[0]

class TT10Float(TT):
    def get(t):
        return unpack("!H", t.data[0:2])[0] / 10.0

class TTError(TT):
    def get(t):
        errno = t.data[1]
        if t.data == [0x6b, 0x7f, 0x06]:
            return f"{errno}: Legionelni teplota"
        if t.data == [0x6b, 0x69, 0x05]:
            return f"{errno}: Nizky tlak vody"
        #if t == [0x9b, 0x05, 0x09]: # Status pri teto chybe
        return f"{errno}: Neznama chyba"

class TTStat2():
    def get(t):
        stby = bool(t.data[10] & 0x08)
        temp = get_temp(t.data[0:2])
        pressure = get_float_decimal(t.data[3:4])
        # Exterior temperature, water pressure
        return f"ET: {temp:5.1f}, WP.: {pressure:.1f}"

class TTHotWater():
    def get(t):
        s = ("charging" if t.data[1] & 0x08 else "ready")
        s += ("" if t.data[1] & 0x04 else ", stby") # Also status byte is 0 in stby mode?
        return s

class TTStat1():
    def get(t):
        return "Horak: {0}".format(2 if t.data[0] & 0x10 else (1 if t.data[0] & 0x04 else 0))
