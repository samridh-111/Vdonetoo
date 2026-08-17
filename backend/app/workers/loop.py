"""Every Celery task body is async, but Celery itself is sync. Calling
`asyncio.run(...)` separately in each task would create a brand-new event
loop per task -- and since the DB engine (app/core/db.py) is cached and
holds a connection pool bound to whichever loop created it, a second task's
fresh loop can't reuse a pool created inside the first task's now-closed
loop (`RuntimeError: Future attached to a different loop`).

Instead, each worker process keeps exactly one long-lived event loop and
runs every task's coroutine on it via `run_until_complete`, so the DB
engine's pool stays valid for the lifetime of the process."""

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

_T = TypeVar("_T")

_loop: asyncio.AbstractEventLoop | None = None


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
    return _loop


def run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    return _get_worker_loop().run_until_complete(coro)


def reset_worker_loop() -> None:
    """Called on `worker_process_init` -- a forked child process inherits
    the parent's `_loop` object in memory, but that loop's underlying OS
    resources aren't valid for the child, so it must be discarded and
    re-created fresh on first use."""
    global _loop
    _loop = None
