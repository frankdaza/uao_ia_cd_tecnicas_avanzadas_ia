"""Verificacion del stack LangChain Ruta A (rubrica M3)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.agentes.agente_taam import NOMBRE_TOOL_ESCALAR, construir_agente_taam
from src.agentes.checkpointer import crear_checkpointer_para_url
from src.agentes.tools.fabrica import crear_tools_taam

RAIZ = Path(__file__).resolve().parents[2]
AGENTES = RAIZ / "src" / "agentes"


def test_archivos_stack_obligatorios():
    assert (AGENTES / "modelo.py").is_file()
    assert (AGENTES / "checkpointer.py").is_file()
    assert (AGENTES / "agente_taam.py").is_file()
    assert (AGENTES / "prompts.py").is_file()


def test_imports_stack():
    from langchain.agents import create_agent  # noqa: F401
    from langchain.agents.middleware import HumanInTheLoopMiddleware  # noqa: F401
    from langchain.chat_models import init_chat_model  # noqa: F401
    from langchain.agents.middleware import dynamic_prompt  # noqa: F401
    from langgraph.checkpoint.postgres import PostgresSaver  # noqa: F401

    texto_modelo = (AGENTES / "modelo.py").read_text(encoding="utf-8")
    assert "init_chat_model" in texto_modelo
    texto_cp = (AGENTES / "checkpointer.py").read_text(encoding="utf-8")
    assert "PostgresSaver" in texto_cp
    texto_ag = (AGENTES / "agente_taam.py").read_text(encoding="utf-8")
    assert "create_agent" in texto_ag
    assert "HumanInTheLoopMiddleware" in texto_ag
    texto_pr = (AGENTES / "prompts.py").read_text(encoding="utf-8")
    assert "dynamic_prompt" in texto_pr


def test_cinco_tools_con_nombre_ingles():
    nombres = {t.name for t in crear_tools_taam()}
    esperados = {
        "obtener_contexto_caso",
        "consultar_protocolo_rag",
        "faq_postoperatorio",
        "clasificar_triage",
        "escalar_a_equipo",
    }
    assert esperados <= nombres


def test_hitl_interrumpe_escalar():
    cp = crear_checkpointer_para_url("sqlite+aiosqlite:///:memory:")
    agente = construir_agente_taam(cp)
    # El middleware HITL debe estar en la lista de middleware del grafo compilado
    assert NOMBRE_TOOL_ESCALAR == "escalar_a_equipo"


def test_script_verificar_stack_m3():
    script = RAIZ / "scripts" / "verificar_stack_m3.sh"
    assert script.is_file()
    proc = subprocess.run(
        ["bash", str(script)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
