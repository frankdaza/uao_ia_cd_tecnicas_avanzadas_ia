"""Tests del meta-prompt del router (JSON + Pydantic + cache por mtime)."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.agentes.meta_prompt import (
    ArchivoMetaPromptAusenteError,
    MetaPromptConfig,
    cargar_meta_prompt_config,
    limpiar_cache_meta_prompt,
    obtener_ruta_meta_prompt_defecto,
)


def _payload_meta_prompt_minimo_valido(
    *,
    modelo_router: str = "gpt-4o-mini",
) -> dict[str, Any]:
    """JSON minimo que cumple el schema (textos cortos salvo ``system_prompt``)."""
    return {
        "version": 1,
        "modelo_router": modelo_router,
        "system_prompt": (
            "Eres el router. No emitas texto libre: solo tool-calls. "
            "Elige faq_estructurada para datos puntuales y rag_denso para corpus amplio. "
            "Instrucciones sinteticas para pruebas." + ("x" * 40)
        ),
        "herramientas": [
            {
                "name": "faq_estructurada",
                "description": "FAQ JSON determinista.",
                "when_to_use": "Datos puntuales institucionales.",
                "ejemplos": ["Telefono PBX"],
            },
            {
                "name": "rag_denso",
                "description": "RAG denso Qdrant.",
                "when_to_use": "Consultas abiertas sobre documentacion.",
                "ejemplos": ["Politica de calidad"],
            },
        ],
        "reglas_decision": ["Priorizar FAQ cuando aplique match directo."],
        "respuesta_sin_contexto": "No tengo información suficiente",
        "saludo_template": "Hola {nombre}, bienvenido.",
    }


@pytest.fixture(autouse=True)
def _limpiar_cache_meta_prompt() -> Iterator[None]:
    limpiar_cache_meta_prompt()
    yield
    limpiar_cache_meta_prompt()


def test_carga_json_versionado_en_repo() -> None:
    ruta = obtener_ruta_meta_prompt_defecto()
    assert ruta.is_file()
    cfg = cargar_meta_prompt_config(ruta)
    assert cfg.version == 1
    nombres = {h.name for h in cfg.herramientas}
    assert nombres == {"faq_estructurada", "rag_denso"}
    assert cfg.respuesta_sin_contexto == "No tengo información suficiente"
    assert "{nombre}" in cfg.saludo_template
    assert "tool-calls" in cfg.system_prompt.lower()


def test_json_invalido(tmp_path: Path) -> None:
    mal = tmp_path / "router_meta_prompt.json"
    mal.write_text("{ no es json ", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON invalido"):
        cargar_meta_prompt_config(mal)


def test_archivo_ausente(tmp_path: Path) -> None:
    with pytest.raises(ArchivoMetaPromptAusenteError):
        cargar_meta_prompt_config(tmp_path / "router_meta_prompt.json")


def test_version_inesperada(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    data = _payload_meta_prompt_minimo_valido()
    data["version"] = 2
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_meta_prompt_config(p)


def test_configuracion_incompleta_falta_clave(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    data = _payload_meta_prompt_minimo_valido()
    del data["system_prompt"]
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_meta_prompt_config(p)


def test_herramientas_incompletas(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    data = _payload_meta_prompt_minimo_valido()
    data["herramientas"] = [data["herramientas"][0]]
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_meta_prompt_config(p)


def test_respuesta_sin_contexto_no_canonica(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    data = _payload_meta_prompt_minimo_valido()
    data["respuesta_sin_contexto"] = "No se"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_meta_prompt_config(p)


def test_saludo_template_sin_placeholder_nombre(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    data = _payload_meta_prompt_minimo_valido()
    data["saludo_template"] = "Hola usuario"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_meta_prompt_config(p)


def test_cache_misma_instancia_cuando_mtime_igual(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    p.write_text(json.dumps(_payload_meta_prompt_minimo_valido()), encoding="utf-8")
    a = cargar_meta_prompt_config(p)
    b = cargar_meta_prompt_config(p)
    assert a is b


def test_cache_recarga_tras_touch_sin_cambiar_contenido(tmp_path: Path) -> None:
    """El criterio pide invalidar por mtime: ``touch`` debe forzar nueva instancia."""
    p = tmp_path / "router_meta_prompt.json"
    p.write_text(json.dumps(_payload_meta_prompt_minimo_valido()), encoding="utf-8")
    c1 = cargar_meta_prompt_config(p)
    time.sleep(0.05)
    p.touch()
    c2 = cargar_meta_prompt_config(p)
    assert c1 is not c2
    assert c1.model_dump() == c2.model_dump()


def test_cache_recarga_despues_de_touch(tmp_path: Path) -> None:
    p = tmp_path / "router_meta_prompt.json"
    base = _payload_meta_prompt_minimo_valido(modelo_router="antes")
    p.write_text(json.dumps(base), encoding="utf-8")
    c1 = cargar_meta_prompt_config(p)
    time.sleep(0.05)
    base["modelo_router"] = "despues"
    p.write_text(json.dumps(base), encoding="utf-8")
    c2 = cargar_meta_prompt_config(p)
    assert c1 is not c2
    assert c1.modelo_router == "antes"
    assert c2.modelo_router == "despues"


def test_modelo_pydantic_rechaza_tipo_raiz_incorrecto() -> None:
    with pytest.raises(ValidationError):
        MetaPromptConfig.model_validate([])
