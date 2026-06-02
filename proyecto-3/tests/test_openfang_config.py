"""Pruebas del TOML versionado de OpenFang (sin binario)."""

from __future__ import annotations

import tomllib
from pathlib import Path

_RUTA_OPENFANG_TOML = (
    Path(__file__).resolve().parents[1] / "openfang" / "openfang.toml"
)


def _cargar_config() -> dict:
    texto = _RUTA_OPENFANG_TOML.read_text(encoding="utf-8")
    return tomllib.loads(texto)


def test_openfang_toml_existe_y_parsea() -> None:
    assert _RUTA_OPENFANG_TOML.is_file()
    cfg = _cargar_config()
    assert isinstance(cfg, dict)


def test_default_model_openai() -> None:
    modelo = _cargar_config()["default_model"]
    assert modelo["provider"] == "openai"
    assert modelo["api_key_env"] == "OPENAI_API_KEY"
    assert "gpt" in modelo["model"]


def test_dashboard_puerto_4200() -> None:
    assert "4200" in _cargar_config()["api_listen"]


def test_canal_telegram_sin_secretos() -> None:
    telegram = _cargar_config()["channels"]["telegram"]
    assert telegram["bot_token_env"] == "TELEGRAM_BOT_TOKEN"
    assert telegram["default_agent"] == "bot_lili_taam"
    contenido = _RUTA_OPENFANG_TOML.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=" not in contenido
    assert "sk-" not in contenido


def test_memoria_decay_configurado() -> None:
    memoria = _cargar_config()["memory"]
    assert memoria["decay_rate"] == 0.05
