import time
import queue
from typing import Optional, Any
from collections.abc import Callable
import traceback
import threading
import logging
import concurrent.futures

from .driver import BsbDriver
from .messages import messages_by_name
from .telegram import Telegram, Command, Message
from .utils.testdriver import TestBsbDriver


logger = logging.getLogger("BSB")
#logging.basicConfig(level=logging.INFO)


class Bsb():
    def __init__(self, port: str):
        self.callbacks: list[Callable[[str, Any], None]] = []
        self.loggers: list[Callable[[Telegram], None]] = []

        self._drv = TestBsbDriver() if port == "TEST" else BsbDriver(port)
        self._requests: list[tuple[Message, Optional[Any], bool, dict[str, Any], queue.Queue[Any]]] = []
        self._mon_requests: dict[Message, int | None] = {}
        self._mon_refresh: dict[Message, float | None] = {}

        self._monitor_thread_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor)

        self._pending_set: dict[tuple[str, int, int], tuple[int | float, Any]] = {}
        self._tpe = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def start(self) -> None:
        self._monitor_thread.start()

    def stop(self) -> None:
        self._monitor_thread_event.set()
        self._monitor_thread.join()

    def get_value(self, req: str, src: int = Telegram.DEF_SRC) -> Any:
        msg = messages_by_name[req]
        kwargs = {'src': src}
        q: queue.Queue[Any] = queue.Queue()
        self._requests.append((msg, None, False, kwargs, q))
        val = q.get()
        return val

    def set_value(self, req: str, value: Any, cmd: Command = Command.SET, src: int = Telegram.DEF_SRC) -> None:
        msg = messages_by_name[req]
        kwargs = {'src': src, 'cmd': cmd}
        q: queue.Queue[Any] = queue.Queue()
        self._requests.append((msg, value, True, kwargs, q))
        v = q.get()
        if isinstance(v, Exception):
            raise v

    def set_monitored(self, monitor: dict[Message, int | None]) -> None:
        self._mon_requests = {}
        self._mon_requests.update(monitor)

    def _monitor(self) -> None:
        while not self._monitor_thread_event.is_set():
            try:
                telegram = self._get_telegram()
                if not self._handle_requests() and telegram is None:
                    time.sleep(0.1)
                self._refresh()
                self._clean_pending_timeout()
            except Exception as e:
                logger.warn("monitor thread: " + str(e))
                logger.warn(traceback.format_exc())

    def _log(self, telegram: Telegram) -> None:
        key = (telegram.name, telegram.src, telegram.dst)
        val = (time.time(), telegram.value)

        if telegram.cmd == Command.SET:
            self._pending_set.update({key: val})

        if telegram.cmd == Command.ACK:
            set_key = (telegram.name, telegram.dst, telegram.src)
            set_value = self._pending_set.get(set_key, None)
            if set_value:
                del self._pending_set[set_key]
                for cb_c in self.callbacks:
                    self._tpe.submit(cb_c, set_key[0], set_value[1])

        for cb_l in self.loggers:
            self._tpe.submit(cb_l, telegram)

    def _clean_pending_timeout(self) -> None:
        clear = []
        current_time = time.time()
        for pending in self._pending_set.items():
            if current_time > pending[1][0] + 5:
                clear.append(pending[0])

        for item in clear:
            del self._pending_set[item]

    def _flush_input(self) -> None:
        while True:
            telegram = self._get_telegram(wait=True)
            if not telegram:
                break

    def _send_telegram(self, telegram: Telegram) -> bool:
        self._flush_input()

        if self._drv.send_telegram(telegram):
            self._log(telegram)
            return True
        return False

    def _get_telegram(self, wait: bool = True) -> Optional[Telegram]:
        telegram = self._drv.receive_telegram(wait)

        if telegram:
            self._log(telegram)

        return telegram

    def _get_value(self, msg: Message, src: int = Telegram.DEF_SRC) -> Any:
        get = Telegram(msg, src=src)
        if not self._send_telegram(get):
            logger.warn(f"get_value: Can't send telegram: {get}")
            raise Exception

        timeout = 0
        ret = self._get_telegram()
        while ret is None or ret.msg.param != get.msg.param:
            ret = self._get_telegram()
            time.sleep(0.1)
            timeout += 1
            if timeout >= 10:
                logger.error(f"get_value: timeout: {get}")
                raise Exception

        return ret.value

    def _set_value(self, msg: Message, value: Any, cmd: Command = Command.SET, src: int = Telegram.DEF_SRC) -> bool:
        telegram = Telegram(msg, cmd=cmd, src=src)
        if not telegram.set_value(value):
            return False

        ret = self._send_telegram(telegram)
        if not ret:
            return False

        if telegram.cmd == Command.INF:
            return True

        timeout = 0
        t = self._get_telegram()
        while (t is None or t.msg.param != msg.param) and timeout < 10:
            if t:
                logger.info(f"set_value: another telegram received: {t}")
            # TODO: Timeout
            t = self._get_telegram()
            time.sleep(0.1)
            timeout += 1
        if timeout == 10:
            logger.error(f"set_value: timeout: {t}")
        return True

    def _handle_requests(self) -> bool:
        if not self._requests:
            return False

        while self._requests:
            try:
                msg, value, do_set, kwargs, q = self._requests.pop()
            except Exception as e:
                logger.warn("handle request GET: " + str(e))
                logger.warn(traceback.format_exc())
                continue

            try:
                if do_set:
                    self._set_value(msg, value, **kwargs)
                else:
                    value = self._get_value(msg, **kwargs)
            except Exception as e:
                q.put(Exception(e))
                raise e
            else:
                q.put(value)

            try:
                for cb in self.callbacks:
                    self._tpe.submit(cb, msg.name, value)
            except Exception as e:
                logger.warn("handle request: " + str(e))
                logger.warn(traceback.format_exc())

        return True

    def _refresh(self) -> None:
        requests = self._mon_requests

        for msg, interval in requests.items():
            if self._monitor_thread_event.is_set():
                break
            current_time = time.time()
            next_refresh = self._mon_refresh.get(msg, 0)
            if next_refresh is not None and current_time >= next_refresh:
                self._mon_refresh[msg] = current_time + interval if interval is not None else None
                try:
                    val = self._get_value(msg)
                except Exception as e:
                    logger.warn("refresh - get_value: " + str(e))
                    logger.warn(traceback.format_exc())
                else:
                    for cb in self.callbacks:
                        self._tpe.submit(cb, msg.name, val)
