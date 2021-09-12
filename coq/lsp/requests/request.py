from asyncio import Condition
from collections import defaultdict
from dataclasses import dataclass
from itertools import count
from typing import Any, AsyncIterator, MutableMapping, Optional, Sequence, Tuple

from pynvim.api.nvim import Nvim
from pynvim_pp.lib import async_call, go
from std2.pickle import new_decoder

from ...registry import rpc
from ...server.rt_types import Stack
from ...shared.timeit import timeit


@dataclass(frozen=True)
class _Session:
    uid: int
    done: bool
    acc: Sequence[Tuple[Optional[str], Any]]


@dataclass(frozen=True)
class _Payload:
    method: str
    uid: int
    client: Optional[str]
    done: bool
    reply: Any


_UIDS = count()
_CONDS: MutableMapping[str, Condition] = {}
_STATE: MutableMapping[str, _Session] = defaultdict(
    lambda: _Session(uid=-1, done=True, acc=())
)

_DECODER = new_decoder[_Payload](_Payload)


@rpc(blocking=False)
def _lsp_notify(nvim: Nvim, stack: Stack, rpayload: _Payload) -> None:
    payload = _DECODER(rpayload)

    async def cont() -> None:
        cond = _CONDS.setdefault(payload.method, Condition())
        acc = _STATE[payload.method]
        if payload.uid == acc.uid:
            _STATE[payload.method] = _Session(
                uid=payload.uid,
                done=payload.done,
                acc=(*acc.acc, (payload.client, payload.reply)),
            )
        async with cond:
            cond.notify_all()

    go(nvim, aw=cont())


async def async_request(
    nvim: Nvim, method: str, *args: Any
) -> AsyncIterator[Tuple[Optional[str], Any]]:
    with timeit(f"LSP :: {method}"):
        uid, done = next(_UIDS), False
        cond = _CONDS.setdefault(method, Condition())

        _STATE[method] = _Session(uid=uid, done=done, acc=())
        async with cond:
            cond.notify_all()

        def cont() -> None:
            nvim.api.exec_lua(f"{method}(...)", (method, uid, *args))

        await async_call(nvim, cont)

        while True:
            acc = _STATE[method]
            if acc.uid == uid:
                for client, a in acc.acc:
                    yield client, a
                if done:
                    break
            elif acc.uid > uid:
                break

            async with cond:
                await cond.wait()
