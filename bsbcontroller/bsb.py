import time
import queue
import traceback
import threading
import logging
import concurrent.futures

from .driver import BsbDriver
from .messages import messages_by_name
from .telegram import Telegram, Command


logger = logging.getLogger("BSB")
#logging.basicConfig(level=logging.INFO)


class Bsb():
    def __init__(self, port):
        self.callbacks = []
        self.loggers = []
        self.requests = {}  # Monitored request: {name: refresh_time}

        self._drv = BsbDriver(port)
        self._requests = []
        self._mon_requests = {}
        self._mon_refresh = {}

        self._monitor_thread_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor)

        self._pending_set = {}
        self._tpe = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def start(self):
        self._monitor_thread.start()

    def stop(self):
        self._monitor_thread_event.set()
        self._monitor_thread.join()

    def get_value(self, req, **kwargs) -> None:
        q = queue.Queue()
        self._requests.append((req, None, False, kwargs, q))
        val = q.get()
        return val

    def set_value(self, req, value, **kwargs) -> None:
        q = queue.Queue()
        self._requests.append((req, value, True, kwargs, q))
        return q.get()

    def set_monitored(self, monitor: dict) -> None:
        for key in monitor:
            # Check if message exists
            messages_by_name[key]

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
                for cb in self.callbacks:
                    self._tpe.submit(cb, set_key[0], set_value[1])

        for cb in self.loggers:
            self._tpe.submit(cb, telegram)

    def _clean_pending_timeout(self):
        clear = []
        current_time = time.time()
        for pending in self._pending_set.items():
            if current_time > pending[1][0] + 5:
                clear.append(pending[0])

        for item in clear:
            del self._pending_set[item]

    def _flush_input(self):
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

    def _get_telegram(self, wait=True):
        telegram = self._drv.receive_telegram(wait)

        if telegram:
            self._log(telegram)

        return telegram

    def _get_value(self, req, **kwargs):
        telegram_kwargs = {}
        if "src" in kwargs:
            telegram_kwargs['src'] = kwargs["src"]
        get = Telegram(messages_by_name[req], **telegram_kwargs)
        if not self._send_telegram(get):
            logger.warn(f"get_value: Can't send telegram: {get}")
            raise Exception

        timeout = 0
        ret = self._get_telegram()
        while (ret is None or ret.param != get.param) and timeout < 10:
            ret = self._get_telegram()
            time.sleep(0.1)
            timeout += 1
        if timeout >= 10:
            logger.error(f"get_value: timeout: {get}")
            raise Exception
        return ret.value

    def _set_value(self, req, value, **kwargs):
        param = messages_by_name[req]
        cmd = kwargs['cmd'] if "cmd" in kwargs else Command.SET
        telegram_kwargs = {}
        if "src" in kwargs:
            telegram_kwargs['src'] = kwargs['src']

        telegram = Telegram(param, cmd=cmd, **telegram_kwargs)
        if not telegram.set_value(value):
            return False

        ret = self._send_telegram(telegram)
        if not ret:
            return False

        if telegram.cmd == Command.INF:
            return True

        timeout = 0
        t = self._get_telegram()
        while (t is None or t.param != param) and timeout < 10:
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
                request, value, do_set, kwargs, q = self._requests.pop()
            except:
                logger.warn("handle request GET: " + str(e))
                logger.warn(traceback.format_exc())
                continue

            try:
                if do_set:
                    self._set_value(request, value, **kwargs)
                else:
                    value = self._get_value(request, **kwargs)
            except Exception as e:
                q.put(Exception(e))
                raise e
            else:
                q.put(value)

            try:
                for cb in self.callbacks:
                    self._tpe.submit(cb, request, value)
            except Exception as e:
                logger.warn("handle request: " + str(e))
                logger.warn(traceback.format_exc())

        return True

    def _refresh(self):
        requests = self._mon_requests

        for req, interval in requests.items():
            if self._monitor_thread_event.is_set():
                break
            current_time = time.time()
            next_refresh = self._mon_refresh.get(req, 0)
            if next_refresh is not None and current_time >= next_refresh:
                self._mon_refresh[req] = current_time + interval if interval is not None else None
                try:
                    val = self._get_value(req)
                except Exception as e:
                    logger.warn("refresh - get_value: " + str(e))
                    logger.warn(traceback.format_exc())
                else:
                    for cb in self.callbacks:
                        self._tpe.submit(cb, req, val)
