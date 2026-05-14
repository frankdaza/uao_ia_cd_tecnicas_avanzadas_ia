"""Pruebas del reranker cross-encoder con mock (sin descargar pesos)."""

from __future__ import annotations

import pytest

from src.rag import reranker_cross_encoder as mod


class _CrossEncoderFalso:
    def __init__(self, modelo: str) -> None:
        self.modelo = modelo

    def predict(self, pares: list[list[str]]) -> list[float]:
        return [float(len(p[1])) for p in pares]


def test_puntuar_orden_por_longitud_de_texto(monkeypatch: pytest.MonkeyPatch) -> None:
    mod.RerankerCrossEncoder.reiniciar_singletons_prueba()
    monkeypatch.setattr(mod, "_importar_cross_encoder", lambda: _CrossEncoderFalso)
    rnk = mod.RerankerCrossEncoder("modelo-falso")
    scores = rnk.puntuar("consulta", ["a", "bbb", "cc"])
    assert scores == [1.0, 3.0, 2.0]


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
