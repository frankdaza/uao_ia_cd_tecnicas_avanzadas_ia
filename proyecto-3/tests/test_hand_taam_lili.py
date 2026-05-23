"""Pruebas estaticas del Hand taam_lili_hand (HAND.toml, SKILL, playbooks)."""

from __future__ import annotations

from pathlib import Path

from src.prompts.validar_hand import (
    EVERY_SECS_DEMO,
    NOMBRE_HAND,
    PALABRAS_ALARMA_CANONICAS,
    TZ_DEMO,
    cargar_hand_toml,
    ruta_hand_dir,
    validar_hand_manifest,
    validar_skill_md,
)

_RAIZ = Path(__file__).resolve().parents[1]


def test_hand_toml_existe_y_parsea() -> None:
    cfg = cargar_hand_toml(_RAIZ)
    assert isinstance(cfg, dict)
    assert cfg["hand"]["name"] == NOMBRE_HAND


def test_hand_schedule_every_secs_bogota() -> None:
    schedule = cargar_hand_toml(_RAIZ)["schedule"]
    assert schedule["every_secs"] == EVERY_SECS_DEMO
    assert schedule["tz"] == TZ_DEMO


def test_hand_capabilities() -> None:
    caps = cargar_hand_toml(_RAIZ)["capabilities"]
    assert caps["recordatorio_postoperatorio"] is True
    assert caps["requerir_evidencia_texto"] is True


def test_hand_guardrails() -> None:
    guardrails = cargar_hand_toml(_RAIZ)["guardrails"]
    assert guardrails["no_diagnostico"] is True
    assert guardrails["disclaimer_obligatorio"] is True
    lista = guardrails["escalar_palabras_alarma"]
    assert isinstance(lista, list)
    for frase in PALABRAS_ALARMA_CANONICAS:
        assert frase in lista


def test_hand_manifest_validacion_completa() -> None:
    faltantes = validar_hand_manifest(_RAIZ)
    assert faltantes == [], f"Manifesto HAND: {faltantes}"


def test_hand_prompts_archivos_existen() -> None:
    hand_dir = ruta_hand_dir(_RAIZ)
    prompts = cargar_hand_toml(_RAIZ)["prompts"]
    for clave in ("recordatorio_postoperatorio", "requerir_evidencia_texto"):
        rel = prompts[clave]
        ruta = hand_dir / rel
        assert ruta.is_file(), clave
        assert len(ruta.read_text(encoding="utf-8").strip()) > 50


def test_skill_md_contenido_minimo() -> None:
    faltantes = validar_skill_md(_RAIZ)
    assert faltantes == [], f"SKILL.md: {faltantes}"


def test_playbooks_mencionan_disclaimer_y_alarma() -> None:
    hand_dir = ruta_hand_dir(_RAIZ)
    for nombre in ("recordatorio_postop.md", "requerir_evidencia.md"):
        texto = (hand_dir / "prompts" / nombre).read_text(encoding="utf-8").lower()
        assert "entrada hand" in texto
        assert "no reemplaza" in texto or "medico tratante" in texto
        assert "dolor intenso" in texto
        assert "fiebre alta" in texto


def test_playbook_evidencia_menciona_solo_texto_y_24h() -> None:
    texto = (
        ruta_hand_dir(_RAIZ) / "prompts" / "requerir_evidencia.md"
    ).read_text(encoding="utf-8").lower()
    assert "solo texto" in texto or "solo acepta texto" in texto
    assert "24" in texto
    assert "pendiente_evidencia" in texto
