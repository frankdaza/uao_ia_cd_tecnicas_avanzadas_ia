"""Pruebas ligeras de la app Gradio (sin levantar servidor)."""

from __future__ import annotations

import importlib
import inspect

import gradio as gr


def test_modulo_expone_blocks_y_manejador() -> None:
    mod = importlib.import_module("src.app.app_gradio")
    assert isinstance(mod.demo, gr.Blocks)
    param_nombres = list(inspect.signature(mod.manejar_pregunta).parameters)
    assert param_nombres == ["texto_pregunta", "modelo_elegido", "prompt_actual"]


def test_pregunta_vacia_devuelve_mensaje() -> None:
    mod = importlib.import_module("src.app.app_gradio")
    t, meta = mod.manejar_pregunta("   ", "llama3.1:8b", "x")
    assert "escribe" in t.lower() or "pregunta" in t.lower()
    assert meta == ""
