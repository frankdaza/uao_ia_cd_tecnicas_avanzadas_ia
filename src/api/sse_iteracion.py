"""Ejecutar iteradores síncronos (LLM streaming) dentro de corrutinas SSE asyncio."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator, Callable, Iterator
from typing import TypeVar

T = TypeVar("T")


class _StreamFinSentinela:
    """Marcador interno terminal de la cola (no sale al consumidor)."""


_SENTINEL = _StreamFinSentinela()


def async_iter_desde_factory(
    factory: Callable[[], Iterator[T]],
    *,
    disconnect_event: asyncio.Event | None = None,
) -> AsyncIterator[T | BaseException]:
    """
    Recorre ``factory()`` en un hilo (``asyncio.to_thread``) y entrega elementos al llamador asíncrono.

    Si el iterador síncrono lanza, se propagará esa excepción como siguiente elemento antes de cerrar.
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[T | BaseException | _StreamFinSentinela] = asyncio.Queue(
        maxsize=64
    )
    shutdown = threading.Event()

    def ejecutor_sync() -> None:
        try:
            for elemento in factory():
                if shutdown.is_set():
                    break
                if disconnect_event is not None and disconnect_event.is_set():
                    break
                fut = asyncio.run_coroutine_threadsafe(queue.put(elemento), loop)
                fut.result()
        except Exception as exc:  # noqa: BLE001 — propagamos al SSE como error
            asyncio.run_coroutine_threadsafe(queue.put(exc), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(_SENTINEL), loop).result()

    async def iterador() -> AsyncIterator[T | BaseException]:
        tarea = asyncio.create_task(asyncio.to_thread(ejecutor_sync))
        try:
            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    break
                yield item
        finally:
            shutdown.set()
            await tarea

    return iterador()
