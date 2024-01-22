import time
import re
import traceback
import threading

from .driver import BsbDriver
from .messages import messages, messages_by_name
from .datatypes import *
from .telegram import Telegram, Command


class Bsb():
    def __init__(self, port):
        self.callbacks = []
        self.loggers = []
        self.requests = {} # Monitored request: {name: refresh_time}

        self._drv = BsbDriver(port)
        self._requests = []
        self._mon_requests = {}
        self._mon_refresh = {}

        self._monitor_thread_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor)

        self._pending_set = {}

    def start(self):
        self._monitor_thread.start()

    def stop(self):
        self._monitor_thread_event.set()
        self._monitor_thread.join()

    def set_value(self, req, value) -> None:
        self._requests.append((req, value))
        # TODO: read from return Queue

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
                if not self._handle_requests() and telegram == None:
                    time.sleep(0.1)
                self._refresh()
                self._clean_pending_timeout()
            except Exception as e:
                print(e)
                print(traceback.format_exc())


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
                    cb(set_key[0], set_value[1])
            
        for cb in self.loggers:
            cb(telegram)

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

    def _get_value(self, req):
        get = Telegram(messages_by_name[req])
        if not self._send_telegram(get):
            print("Can't send telegram")
            return None
        
        timeout = 0
        ret = self._get_telegram()
        while (ret == None or ret.param != get.param) and timeout < 10:
            ret = self._get_telegram()
            time.sleep(0.1)
            timeout += 1
        if timeout == 10:
            print("Timeout")
            return None
        return ret.value

    def _set_value(self, req, value):
        param = messages_by_name[req]
        telegram = Telegram(param, cmd=Command.SET)
        if not telegram.set_value(value):
            return False

        #print(telegram.to_raw()
        print([f"{x:02X}" for x in telegram.to_raw()])

        ret = self._send_telegram(telegram)

        timeout = 0
        t = self._get_telegram()
        while (t == None or t.param != param) and timeout < 10:
            if t:
                print(t)
            # TODO: Timeout
            t = self._get_telegram()
            time.sleep(0.1)
            timeout += 1
        if timeout == 10:
            print("BSB set value: Timeout")
        return True

    def _handle_requests(self) -> bool:
        if not self._requests:
            return False

        while self._requests:
            request, value = self._requests.pop()
            self._set_value(request, value)
            for cb in self.callbacks:
                cb(request, value)
        return True

    def _refresh(self):
        requests = self._mon_requests

        for req, interval in requests.items():
            if self._monitor_thread_event.is_set():
                break
            current_time = time.time()
            next_refresh = self._mon_refresh.get(req, 0)
            if next_refresh != None and current_time >= next_refresh:
                self._mon_refresh[req] = current_time + interval if interval != None else None
                val = self._get_value(req)
                if val != None:
                    for cb in self.callbacks:
                        cb(req, val)
