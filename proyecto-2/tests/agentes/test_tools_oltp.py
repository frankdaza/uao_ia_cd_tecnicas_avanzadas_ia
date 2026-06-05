"""Pruebas unitarias de tools (sin LLM)."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from src.agentes.tools.clasificar_triage import clasificar_triage
from src.agentes.tools.escalar_a_equipo import escalar_a_equipo
from src.agentes.tools.faq_postoperatorio import faq_postoperatorio
from src.agentes.tools.obtener_contexto_caso import obtener_contexto_caso
from src.persistencia.modelos import AlertaTriage


@pytest.mark.asyncio
async def test_obtener_contexto_caso_vinculado(
    factory_sqlite,
    caso_vinculado_telegram_123,
    contexto_agente_123,
):
    salida = await obtener_contexto_caso.ainvoke({})
    assert salida.vinculado is True
    assert salida.paciente_nombre == "Paciente Demo"
    assert salida.nombre_procedimiento == "Hernioplastia demo"
    assert salida.tipo_procedimiento_id is not None


@pytest.mark.asyncio
async def test_faq_postoperatorio_encuentra_intent(contexto_agente_123):
    texto = faq_postoperatorio.invoke({"consulta": "tengo fiebre alta"})
    assert "urgencias" in texto.lower() or "equipo" in texto.lower()


def test_clasificar_triage_urgente():
    salida = clasificar_triage.invoke(
        {"sintomas_descritos": "fiebre alta y sangrado abundante"}
    )
    assert salida.severidad == "urgente"
    assert salida.rationale


def test_clasificar_triage_mucho_sangrado():
    salida = clasificar_triage.invoke(
        {"sintomas_descritos": "Tengo mucho sangrado, creo que se me abrio la herida"}
    )
    assert salida.severidad == "urgente"


@pytest.mark.asyncio
async def test_escalar_a_equipo_crea_alerta(
    factory_sqlite,
    caso_vinculado_telegram_123,
    contexto_agente_123,
):
    salida = await escalar_a_equipo.ainvoke(
        {
            "severidad": "urgente",
            "resumen": "Paciente reporta fiebre alta",
            "mensaje_paciente_ref": "tengo fiebre",
        }
    )
    assert salida.alerta_id
    async with factory_sqlite() as sesion:
        res = await sesion.execute(select(AlertaTriage))
        filas = list(res.scalars().all())
    assert len(filas) == 1
    assert filas[0].severidad == "urgente"
    assert "fiebre" in filas[0].resumen.lower()
