from concurrent.futures import Future, InvalidStateError, ThreadPoolExecutor
from contextlib import suppress
from queue import SimpleQueue
from threading import Lock
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class Executor:
    def __init__(self, pool: ThreadPoolExecutor) -> None:
        self._lock, self._q = Lock(), SimpleQueue()
        pool.submit(self._forever)

    def _forever(self) -> None:
        while True:
            f = self._q.get()
            f()

    def submit(self, f: Callable[..., T], *args: Any, **kwargs: Any) -> T:

        fut = Future()

        def cont() -> None:
            try:
                ret = f(*args, **kwargs)
            except Exception as e:
                with suppress(InvalidStateError):
                    fut.set_exception(e)
            else:
                with suppress(InvalidStateError):
                    fut.set_result(ret)

        self._q.put(cont)
        return fut.result()
