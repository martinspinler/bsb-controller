import time
import queue
import traceback
import logging
from typing import Optional
from serial import Serial, PARITY_ODD

from .telegram import Telegram, CrcError


logger = logging.getLogger("BSB")


class BsbDriver(object):
    BAUD = 4800
    BYTE_TIME = 1 / (BAUD / 11.0)

    def __init__(self, port: str):
        # Timeout if nothing received for ten characters (11 for start+8b+parity+stop bits)
        TIMEOUT = 1. / (self.BAUD / 11) * 10

        self._buffer: list[int] = []
        self._ooo_queue: queue.Queue[Telegram] = queue.Queue()

        self._serial = Serial(port, self.BAUD, timeout=TIMEOUT, parity=PARITY_ODD)

    def receive_telegram(self, wait: bool = True) -> Optional[Telegram]:
        if not self._ooo_queue.empty():
            return self._ooo_queue.get_nowait()

        return self._receive_telegram(wait)

    def _receive_telegram(self, wait: bool = True) -> Optional[Telegram]:
        TIMEOUT = 20

        timeout = TIMEOUT
        buf = self._buffer
        while timeout > 0 and (self._serial.in_waiting > 0 or (wait and buf)):
            data = self._serial.read(1)
            if not data:
                timeout -= 1
                continue

            # Reset timeout
            timeout = TIMEOUT
            byte = data[0] ^ 0xff

            # Wait for SOF
            if not buf and byte != Telegram.SOF:
                continue

            buf.append(byte)
            length = buf[3] if len(buf) > 3 else -1
            if len(buf) == length:
                try:
                    telegram = Telegram.from_raw(bytes(buf))
                    buf.clear()
                except CrcError:
                    logger.warn(f"driver: Telegram CRC error: {buf}")
                    buf.clear()
                except Exception as e:
                    logger.error(f"driver: Telegram error: {e}: {buf}")
                    logger.error(traceback.format_exc())
                    buf.clear()
                else:
                    return telegram

        if timeout == 0:
            logger.warn(f"driver: Timeout {buf}")
            buf.clear()
        return None

    def send_telegram(self, telegram: Telegram, retries: int = 10) -> bool:
        msg = bytes([x ^ 0xff for x in telegram.to_raw()])

        while retries:
            self._serial.write(msg)
            time.sleep(self.BYTE_TIME * len(msg) * 2)
            retries -= 1

            recv: Optional[Telegram] = telegram
            while recv:
                recv = self._receive_telegram(True)
                if recv:
                    if telegram.to_raw() == recv.to_raw():
                        return True
                    else:
                        self._ooo_queue.put_nowait(recv)

            time.sleep(1.567)
            logger.warn(f"driver: sent telegram not received back, resending: {telegram}")

        return False
