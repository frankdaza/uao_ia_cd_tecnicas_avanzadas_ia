"""Pruebas unitarias del repositorio de usuarios con sesion SQLAlchemy simulada."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.persistencia.modelos import Usuario
from src.persistencia.repositorios.usuarios import RepositorioUsuarios


@pytest.mark.asyncio
async def test_actualizar_last_login_ejecuta_update() -> None:
    sesion = AsyncMock()
    repo = RepositorioUsuarios(sesion)
    uid = uuid.uuid4()
    await repo.actualizar_last_login(uid)
    sesion.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_obtener_o_crear_inserta_y_devuelve_ya_existia_false() -> None:
    sesion = AsyncMock()
    nuevo_id = uuid.uuid4()
    fila = Usuario(id=nuevo_id, documento_identidad="abc", nombre="Creado")
    res_insert = MagicMock()
    res_insert.scalar_one_or_none.return_value = nuevo_id
    sesion.execute = AsyncMock(return_value=res_insert)
    sesion.get = AsyncMock(return_value=fila)
    repo = RepositorioUsuarios(sesion)
    usuario, ya_existia = await repo.obtener_o_crear("abc", "Creado")
    assert ya_existia is False
    assert usuario is fila
    sesion.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_obtener_o_crear_conflicto_devuelve_existente_y_flag_true() -> None:
    sesion = AsyncMock()
    existente = Usuario(
        id=uuid.uuid4(),
        documento_identidad="dup",
        nombre="Nombre original",
    )
    res_insert = MagicMock()
    res_insert.scalar_one_or_none.return_value = None
    res_select = MagicMock()
    res_select.scalars.return_value.first.return_value = existente
    sesion.execute = AsyncMock(side_effect=[res_insert, res_select])
    repo = RepositorioUsuarios(sesion)
    usuario, ya_existia = await repo.obtener_o_crear("dup", "Nombre nuevo")
    assert ya_existia is True
    assert usuario is existente
    assert sesion.execute.await_count == 2
