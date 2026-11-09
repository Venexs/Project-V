# logger.py
import queue
import threading
import time
import sys

_log_queue = queue.Queue()

def start_logger_thread():
    def _run():
        while True:
            try:
                level, msg = _log_queue.get()
            except Exception:
                continue
            # We keep printing simple, single-thread writer ensures no interleaving
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"[{timestamp}] [{level}] {msg}", flush=True)
            _log_queue.task_done()
    t = threading.Thread(target=_run, daemon=True, name="LoggerThread")
    t.start()
    return t

def debug(msg): _log_queue.put(("DEBUG", msg))
def info(msg):  _log_queue.put(("INFO", msg))
def warn(msg):  _log_queue.put(("WARN", msg))
def error(msg): _log_queue.put(("ERROR", msg))
