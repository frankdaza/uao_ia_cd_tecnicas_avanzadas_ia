"""Pruebas ligeras de la app Gradio (legacy — deprecada).

El módulo src.app.app_gradio fue movido a src.app.legacy.app_gradio al completar
la migración al frontend React 19 + Vite 7 (task-39). Estas pruebas se conservan
como cobertura histórica del código legacy pero apuntan a la nueva ruta.
"""

from __future__ import annotations

import importlib
import inspect

import gradio as gr
import pytest


@pytest.mark.legacy
def test_modulo_expone_blocks_y_manejador() -> None:
    mod = importlib.import_module("src.app.legacy.app_gradio")
    assert isinstance(mod.demo, gr.Blocks)
    param_nombres = list(inspect.signature(mod.manejar_pregunta).parameters)
    assert param_nombres == ["texto_pregunta", "modelo_elegido", "prompt_actual"]


@pytest.mark.legacy
def test_pregunta_vacia_devuelve_mensaje() -> None:
    mod = importlib.import_module("src.app.legacy.app_gradio")
    t, meta = mod.manejar_pregunta("   ", "llama3.1:8b", "x")
    assert "escribe" in t.lower() or "pregunta" in t.lower()
    assert meta == ""
