# sync.py
import threading
from contextlib import contextmanager

# Global in-process locks (module-level)
_GLOBAL_FILE_LOCK = threading.RLock()
_LOG_LOCK = threading.Lock()

@contextmanager
def file_lock():
    """Use this around any file read/write operation in-process."""
    _GLOBAL_FILE_LOCK.acquire()
    try:
        yield
    finally:
        _GLOBAL_FILE_LOCK.release()

@contextmanager
def log_lock():
    _LOG_LOCK.acquire()
    try:
        yield
    finally:
        _LOG_LOCK.release()
