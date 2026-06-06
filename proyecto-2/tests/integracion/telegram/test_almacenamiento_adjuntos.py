"""Pruebas de almacenamiento en disco de adjuntos TAAM."""

from __future__ import annotations

import uuid

import pytest

from src.configuracion import obtener_configuracion
from src.integracion.telegram.almacenamiento_adjuntos import (
    AdjuntoTelegramInvalidoError,
    guardar_adjunto_en_disco,
    resolver_ruta_segura_adjunto,
)


@pytest.fixture
def cfg_adjunto_pequeno(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TAAM_ADJUNTO_MAX_MB", "1")
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


def test_guardar_imagen_jpeg(cfg_adjunto_pequeno, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src import rutas_workspace

    monkeypatch.setattr(
        rutas_workspace,
        "resolver_ruta_workspace",
        lambda rel: tmp_path / rel,
    )
    caso_id = uuid.uuid4()
    contenido = b"\xff\xd8\xff\xe0" + b"\x00" * 128
    cfg = obtener_configuracion()
    guardado = guardar_adjunto_en_disco(
        caso_id=caso_id,
        contenido=contenido,
        mime_type="image/jpeg",
        cfg=cfg,
    )
    assert guardado.tipo == "imagen"
    assert guardado.tamano_bytes == len(contenido)
    ruta = resolver_ruta_segura_adjunto(guardado.ruta_relativa)
    assert ruta.is_file()


def test_rechaza_mime_no_permitido(cfg_adjunto_pequeno) -> None:
    cfg = obtener_configuracion()
    with pytest.raises(AdjuntoTelegramInvalidoError):
        guardar_adjunto_en_disco(
            caso_id=uuid.uuid4(),
            contenido=b"datos",
            mime_type="application/pdf",
            cfg=cfg,
        )
