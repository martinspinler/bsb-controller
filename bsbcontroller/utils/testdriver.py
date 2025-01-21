import queue
from typing import Optional, Any

from ..telegram import Telegram, Command, Flag
from ..telegram import fields as f


class TestBsbDriver(object):
    def __init__(self) -> None:
        self._ooo_queue: queue.Queue[Telegram] = queue.Queue()

    def receive_telegram(self, wait: bool = True) -> Optional[Telegram]:
        if not self._ooo_queue.empty():
            return self._ooo_queue.get_nowait()

        return self._receive_telegram(wait)

    def _receive_telegram(self, wait: bool = True) -> Optional[Telegram]:
        return None

    def send_telegram(self, telegram: Telegram, retries: int = 10) -> bool:
        cmd = {
            Command.QUR: Command.ANS,
            Command.SET: Command.ACK,
        }.get(telegram.cmd)

        if cmd is not None:
            t = Telegram(telegram.msg, cmd=cmd, dst=telegram.src, src=telegram.dst)

            if telegram.cmd == Command.QUR:
                value: Any
                if t.msg.fields == f.CStatus:
                    value = 'disabled'
                elif t.msg.fields == f.OpMode:
                    value = 'automatic'
                elif t.msg.fields in [f.OnOff, f.Enable]:
                    value = True
                else:
                    value = 42

                t.set_value(value)

                # FIXME: this is only for TestBsbDriver
                if t._intflags & Flag.FB and t.cmd == Command.ANS:
                    t._flags = bytes([1]) if value is None else bytes([0])
                t._update_value()
            elif telegram.cmd == Command.SET:
                pass

            self._ooo_queue.put_nowait(t)
        return True
