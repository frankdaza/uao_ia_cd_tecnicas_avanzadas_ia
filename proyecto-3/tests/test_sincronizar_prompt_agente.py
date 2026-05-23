"""Pruebas del script de sincronizacion prompt -> agent.toml."""

from __future__ import annotations

from pathlib import Path

from src.prompts.validar import (
    extraer_system_prompt_de_agent_toml,
    leer_prompt_desde_system_md,
    normalizar_prompt,
    reemplazar_system_prompt_en_agent_toml,
    sincronizar_agent_toml_desde_system_md,
)

_RAIZ = Path(__file__).resolve().parents[1]


def test_reemplazar_system_prompt_preserva_resto_toml(tmp_path: Path) -> None:
    agent = tmp_path / "agent.toml"
    original = '''name = "test"

[model]
provider = "openai"
system_prompt = """viejo"""

[capabilities]
tools = ["memory_recall"]
'''
    agent.write_text(original, encoding="utf-8")
    nuevo_prompt = "prompt\nnuevo\n"
    actualizado = reemplazar_system_prompt_en_agent_toml(original, nuevo_prompt)
    agent.write_text(actualizado, encoding="utf-8")
    contenido = agent.read_text(encoding="utf-8")
    assert 'name = "test"' in contenido
    assert "memory_recall" in contenido
    assert extraer_system_prompt_de_agent_toml(contenido) == nuevo_prompt


def test_sincronizar_en_directorio_temporal(tmp_path: Path) -> None:
    system_dir = (
        tmp_path / "openfang" / "hands" / "taam_lili_hand" / "prompts"
    )
    agent_dir = tmp_path / "openfang" / "agents" / "bot_lili_taam"
    system_dir.mkdir(parents=True)
    agent_dir.mkdir(parents=True)
    system_md = system_dir / "system.md"
    system_md.write_text(
        "Linea uno.\n\n## Rol\n\n- Usar memory_recall y SOLO contexto.\n",
        encoding="utf-8",
    )
    agent_toml = agent_dir / "agent.toml"
    agent_toml.write_text(
        'system_prompt = """placeholder"""\n[model]\nprovider = "openai"\n',
        encoding="utf-8",
    )
    prompt, ruta = sincronizar_agent_toml_desde_system_md(tmp_path, escribir=True)
    assert "Linea uno" in prompt
    extraido = extraer_system_prompt_de_agent_toml(ruta.read_text(encoding="utf-8"))
    assert normalizar_prompt(extraido) == normalizar_prompt(prompt)


def test_script_sincronizar_idempotente() -> None:
    sincronizar_agent_toml_desde_system_md(_RAIZ, escribir=True)
    prompt_a, _ = sincronizar_agent_toml_desde_system_md(_RAIZ, escribir=False)
    sincronizar_agent_toml_desde_system_md(_RAIZ, escribir=True)
    prompt_b, _ = sincronizar_agent_toml_desde_system_md(_RAIZ, escribir=False)
    assert normalizar_prompt(prompt_a) == normalizar_prompt(prompt_b)
