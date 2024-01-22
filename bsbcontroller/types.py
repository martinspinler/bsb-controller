import enum


class Command(enum.IntEnum):
    QIN = 0x01 # Request info telegram
    INF = 0x02 # Status
    SET = 0x03 # Change
    ACK = 0x04 # Confirm
    NAK = 0x05
    QUR = 0x06 # Query
    ANS = 0x07 # Reply
    ERR = 0x08 # Error

    QRV = 0x0F # Query Reset Value
    ARV = 0x10 # Reply Reset Value
    QRE = 0x11 # Query Reset Value failed
    IQ1 = 0x12 # Internal Query 1
    IA1 = 0x13 # Internal Reply 1
    IQ2 = 0x14 # Internal Query 2
    IA2 = 0x15 # Internal Reply 2

class Flag(enum.IntFlag):
    NONE = 0
    FB = 1
    LB = 2

#class Flag(enum.IntFlag):
#    WRITABLE = 0
#    RDONLY  = 1
#    WRONLY  = 2
#    NO_CMD  = 4
#    OEM     = 8
#    SPEC_INF = 16
#    EEPROM  = 32
#    SW_CTL_RONLY = 128
#
#    def __repr__(self):
#        return '|'.join(val.name for val in Flag if self.value & val)
