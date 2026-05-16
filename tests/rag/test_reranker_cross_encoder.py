"""Pruebas del reranker cross-encoder con mock (sin descargar pesos)."""

from __future__ import annotations

import logging

import pytest

from src.rag.runtime import reranker_cross_encoder as mod


class _CrossEncoderFalso:
    def __init__(self, modelo: str) -> None:
        self.modelo = modelo

    def predict(self, pares: list[list[str]], batch_size: int | None = None, **_kwargs: object) -> list[float]:
        return [float(len(p[1])) for p in pares]


class _CrossEncoderLotes:
    """Registra los ``batch_size`` recibidos y devuelve scores por longitud de texto."""

    def __init__(self, modelo: str) -> None:
        self.modelo = modelo
        self.batch_sizes: list[int | None] = []

    def predict(self, pares: list[list[str]], batch_size: int | None = None, **_kwargs: object) -> list[float]:
        self.batch_sizes.append(batch_size)
        return [float(len(p[1])) for p in pares]


class _CrossEncoderNaNEnMedio:
    def __init__(self, modelo: str) -> None:
        self.modelo = modelo

    def predict(self, pares: list[list[str]], **_kwargs: object) -> list[float]:
        if len(pares) != 3:
            return [1.0 for _ in pares]
        return [0.5, float("nan"), 0.7]


def test_puntuar_orden_por_longitud_de_texto(monkeypatch: pytest.MonkeyPatch) -> None:
    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    monkeypatch.setattr(mod, "_importar_cross_encoder", lambda: _CrossEncoderFalso)
    rnk = mod.RerankerCrossEncoder("modelo-falso")
    scores = rnk.puntuar("consulta", ["a", "bbb", "cc"])
    assert scores == [1.0, 3.0, 2.0]


def test_puntuar_respeta_batch_size_en_predict(monkeypatch: pytest.MonkeyPatch) -> None:
    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    monkeypatch.setattr(mod, "_importar_cross_encoder", lambda: _CrossEncoderLotes)
    rnk = mod.RerankerCrossEncoder("m-lotes")
    textos = ["x"] * 25
    rnk.puntuar("q", textos, batch_size=7)
    assert rnk._encoder is not None  # type: ignore[attr-defined]
    enc = rnk._encoder  # type: ignore[attr-defined]
    assert enc.batch_sizes == [7]


def test_puntuar_descarta_nan_con_warning(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    monkeypatch.setattr(mod, "_importar_cross_encoder", lambda: _CrossEncoderNaNEnMedio)
    rnk = mod.RerankerCrossEncoder("nan-model")
    caplog.set_level(logging.WARNING)
    scores = rnk.puntuar("q", ["a", "b", "c"])
    assert scores[0] == 0.5
    assert scores[1] is None
    assert scores[2] == 0.7
    assert any("reranker.score_no_finito" in r.message for r in caplog.records)


def test_puntuar_lista_vacia() -> None:
    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    rnk = mod.RerankerCrossEncoder("x")
    rnk._encoder = _CrossEncoderFalso("x")  # type: ignore[attr-defined]
    assert rnk.puntuar("q", []) == []


def test_import_fallido_mensaje_instalar_uv(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    real_import = builtins.__import__

    def _bloquear_st(name: str, *args: object, **kwargs: object):
        if name == "sentence_transformers":
            raise ImportError("simulado")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _bloquear_st)
    rnk = mod.RerankerCrossEncoder("cualquiera")
    with pytest.raises(RuntimeError, match=r"uv add sentence-transformers"):
        rnk.puntuar("hola", ["t1"])


def test_singleton_reusa_mismo_encoder(monkeypatch: pytest.MonkeyPatch) -> None:
    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    monkeypatch.setattr(mod, "_importar_cross_encoder", lambda: _CrossEncoderFalso)
    a = mod.RerankerCrossEncoder("mismo")
    b = mod.RerankerCrossEncoder("mismo")
    a._obtener_encoder()
    b._obtener_encoder()
    assert a._encoder is b._encoder
