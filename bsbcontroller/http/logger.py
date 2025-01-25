import datetime
import logging

from typing import Any, Callable

import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json

from .. import Bsb
from ..telegram import Telegram, Command
from ..messages import messages_by_id


logger = logging.getLogger("HAC")


class MyHTTPServer(HTTPServer):
    def __init__(self, logger: "MyLogger", *args: Any, **kwargs: Any) -> None:
        self.logger = logger
        super().__init__(*args, **kwargs)


class MyBaseHTTPRequestHandler(BaseHTTPRequestHandler):
    server: MyHTTPServer


class HttpLogHandler(MyBaseHTTPRequestHandler):
    def _set_headers(self) -> None:
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

    def do_HEAD(self) -> None:
        self._set_headers()

    def do_GET(self) -> None:
        self._set_headers()
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)
        logs = self.server.logger.logs
        bsb = self.server.logger.bsb

        qget = query.get("get")
        qset = query.get("set")
        qval = query.get("val")
        if qget is not None:
            val = bsb.get_value(qget[0])
            self.wfile.write(json.dumps(val, indent=4).encode('utf8'))
            return
        elif qset is not None and qval is not None:
            try:
                val = json.loads(qval[0])
            except Exception:
                try:
                    val = json.loads(qval[0].lower())
                except Exception:
                    val = qval[0]
            bsb.set_value(qset[0], val)
            return

        log = query.get("log", logs.keys())
        msg = query.get("msg", [])
        ex_msg = query.get("exclude", [])

        val = {
            lk: [
                str(t) for t in lv if (not msg or t.name in msg) and (t.name not in ex_msg)
            ] for lk, lv in logs.items() if lk in log
        }

        try:
            self.wfile.write(json.dumps(val, indent=4).encode('utf8'))
        except IOError:
            pass


class ThreadHttpLogServer(threading.Thread):
    def __init__(self, logger: "MyLogger", addr: str = '', port: int = 8008) -> None:
        threading.Thread.__init__(self)

        self.logger = logger
        self.addr = addr
        self.port = port
        self.daemon = True
        self.start()

    def run(self) -> None:
        server = self.server = MyHTTPServer(self.logger, (self.addr, self.port), HttpLogHandler)
        #server.logger = self.logger
        server.serve_forever()


class TelegramLogger:
    def __init__(self, bsb: Bsb, filters: dict[str, tuple[Callable[[Telegram], bool], int]]) -> None:
        self.bsb = bsb
        bsb.loggers.append(self.log_callback)

        filename = "/srv/hac/telegram_log.json"

        self.logs: dict[str, list[Telegram]] = {k: [] for k in filters.keys()}
        self.filters = filters

        if False:
            try:
                self.file = open(filename)
                for ln in self.file.readlines():
                    try:
                        m = json.loads(ln)
                    except Exception as e:
                        logger.warning(f"Can't load json: {e}")
                        continue

                    ts = datetime.datetime.fromtimestamp(m['timestamp'])
                    t = Telegram.from_raw(bytes(m['telegram_raw']), messages_by_id, timestamp=ts)

                    self._append_log(t)
                self.file.close()
            except Exception as e:
                logger.warning(f"Can't load json: {e}")

        #self.file = open("/srv/hac/telegram_log.json", "a")

    def log_callback(self, t: Telegram) -> None:
        self._append_log(t)

    def _append_log(self, t: Telegram) -> None:
        for k, (fn, max_cnt) in self.filters.items():
            log = self.logs[k]
            if fn(t):
                log.append(t)
                if len(log) > max_cnt:
                    log.pop(0)


class MyLogger(TelegramLogger):
    def __init__(self, bsb: Bsb):
        def filter_all(t: Telegram) -> bool:
            if t.cmd == Command.QUR and t.src == 0x42:
                return False
            return True

        def filter_nol(t: Telegram) -> bool:
            if t.cmd == Command.QUR and t.src == 0x42:
                return False
            if t.cmd == Command.ANS and t.dst == 0x42:
                return False

            return True

        def filter_inf(t: Telegram) -> bool:
            if t.cmd != Command.INF:
                return False

            ignored = ["room1_temp_status", "datetime", "hc2_status", "hc3_status"]
            if t.name in ignored:
                return False

            return True

        def filter_unk(t: Telegram) -> bool:
            if not filter_inf(t):
                return False

            if t.name == "status_msg1":
                if t.data in [[x, 0, 0, 0x59] for x in [0, 0x4, 0x14]]:
                    return False
            elif t.name == "hot_water_status":
                if t.data in [[0, x] for x in [0x45, 0x4d]]:
                    return False
            elif t.name == "hc1_status":
                if t.data in [[0, x] for x in [0x45, 0x4d]]:
                    return False
            #else:
            #    return False

            return True

        filters: dict[str, tuple[Callable[[Telegram], bool], int]] = {
            "all": (filter_all, 300),
            "inf": (filter_inf, 3000),
            "unk": (filter_unk, 3000),
            "nol": (filter_nol, 3000),
        }
        super().__init__(bsb, filters)
