"""Plantillas por defecto por tipo de procedimiento (idempotente)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import PlantillaRecordatorio
from src.persistencia.repositorios.plantillas_recordatorio import (
    RepositorioPlantillasRecordatorio,
)

# Offsets en horas desde medianoche UTC del dia de cirugia.
_PLANTILLAS_DEFECTO: tuple[tuple[str, int, str, str], ...] = (
    (
        "medicacion",
        24,
        "Tome la medicacion segun la indicacion de su cirujano.",
        (
            "Hola {nombre_paciente}, recordatorio de medicacion tras su procedimiento "
            "({tipo_procedimiento}): {texto_cuidado}"
        ),
    ),
    (
        "terapia",
        48,
        "Realice las terapias indicadas en su plan de recuperacion.",
        (
            "Hola {nombre_paciente}, recordatorio de terapia ({tipo_procedimiento}): "
            "{texto_cuidado}"
        ),
    ),
    (
        "control",
        168,
        "Revise signos de alarma y asista al control programado.",
        (
            "Hola {nombre_paciente}, recordatorio de control postoperatorio "
            "({tipo_procedimiento}): {texto_cuidado}"
        ),
    ),
)


async def asegurar_plantillas_defecto(
    sesion: AsyncSession,
    tipo_procedimiento_id: uuid.UUID,
) -> list[PlantillaRecordatorio]:
    """
    Inserta plantillas MVP si el tipo aun no tiene ninguna (UC-MVP-04).

    Idempotente: no duplica si ya existen filas para el ``tipo_procedimiento_id``.
    """
    repo = RepositorioPlantillasRecordatorio(sesion)
    existentes = await repo.listar_por_tipo(tipo_procedimiento_id)
    if existentes:
        return existentes

    creadas: list[PlantillaRecordatorio] = []
    for tipo, offset, _texto_cuidado, texto_plantilla in _PLANTILLAS_DEFECTO:
        fila = await repo.crear(
            tipo_procedimiento_id=tipo_procedimiento_id,
            tipo=tipo,
            offset_horas_desde_cirugia=offset,
            texto_plantilla=texto_plantilla,
        )
        creadas.append(fila)
    return creadas


def texto_cuidado_para_plantilla(tipo: str) -> str:
    """Texto de cuidado por defecto segun tipo de plantilla."""
    for t, _, texto, _ in _PLANTILLAS_DEFECTO:
        if t == tipo:
            return texto
    return "Siga las indicaciones de su equipo de salud."
