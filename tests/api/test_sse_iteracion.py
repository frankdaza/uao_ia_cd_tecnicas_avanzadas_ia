"""Comportamiento de async_iter_desde_factory (streaming incremental)."""

from __future__ import annotations

import asyncio

import pytest

from src.api.sse_iteracion import async_iter_desde_factory


@pytest.mark.asyncio
async def test_disconnect_corta_factory_antes_del_fin() -> None:
    disco = asyncio.Event()

    def factory():
        yield 1
        yield 2
        yield 3

    orden: list[int] = []
    disco.set()

    async for elemento in async_iter_desde_factory(factory, disconnect_event=disco):
        if isinstance(elemento, int):
            orden.append(elemento)

    assert orden == []


@pytest.mark.asyncio
async def test_itera_sin_disconnect() -> None:
    def factory():
        yield "a"
        yield "b"

    salida: list[str] = []
    async for elemento in async_iter_desde_factory(factory, disconnect_event=None):
        salida.append(str(elemento))
    assert salida == ["a", "b"]
