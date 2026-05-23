"""Logica de codigos de emparejamiento Telegram (UC-MVP-02)."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.configuracion import Configuracion
from src.persistencia.modelos import CasoPostoperatorio, VinculoTelegram
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

_ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _en_utc(valor: datetime | None) -> datetime | None:
    """Normaliza datetimes naive (SQLite) o aware a UTC."""
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


class EmparejamientoError(Exception):
    """Error de negocio con codigo HTTP y mensaje para Telegram."""

    def __init__(
        self,
        *,
        codigo_error: str,
        mensaje_telegram: str,
        status_http: int,
    ) -> None:
        self.codigo_error = codigo_error
        self.mensaje_telegram = mensaje_telegram
        self.status_http = status_http
        super().__init__(mensaje_telegram)


@dataclass(frozen=True)
class CodigoGenerado:
    codigo: str
    expira_at: datetime
    caso_id: uuid.UUID


@dataclass(frozen=True)
class ResultadoEmparejar:
    caso_id: uuid.UUID
    vinculado_at: datetime
    mensaje_confirmacion: str


def chat_id_placeholder(caso_id: uuid.UUID) -> int:
    """Identificador negativo estable hasta que el paciente empareje."""
    fragmento = int.from_bytes(caso_id.bytes[:8], "big", signed=False)
    return -(fragmento % (2**62)) - 1


def generar_codigo_emparejamiento(longitud: int) -> str:
    longitud = max(6, min(8, longitud))
    return "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(longitud))


async def validar_tipo_procedimiento_indexado(
    sesion: AsyncSession,
    tipo_procedimiento_id: uuid.UUID,
) -> None:
    repo = RepositorioTiposProcedimiento(sesion)
    tipo = await repo.obtener_por_id(tipo_procedimiento_id)
    if tipo is None:
        raise EmparejamientoError(
            codigo_error="tipo_procedimiento_inexistente",
            mensaje_telegram="El tipo de procedimiento no existe.",
            status_http=422,
        )
    if tipo.indexacion_estado != "ok":
        raise EmparejamientoError(
            codigo_error="procedimiento_no_indexado",
            mensaje_telegram=(
                "El protocolo del procedimiento aun no esta listo. "
                "Pida al administrador que complete la indexacion."
            ),
            status_http=422,
        )


async def generar_codigo_para_caso(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
    cfg: Configuracion,
) -> CodigoGenerado:
    repo_casos = RepositorioCasosPostoperatorio(sesion)
    repo_vinculos = RepositorioVinculosTelegram(sesion)

    caso = await repo_casos.obtener_por_id(caso_id)
    if caso is None:
        raise EmparejamientoError(
            codigo_error="caso_inexistente",
            mensaje_telegram="Caso no encontrado.",
            status_http=404,
        )
    if caso.estado != "activo":
        raise EmparejamientoError(
            codigo_error="caso_no_activo",
            mensaje_telegram="Este caso ya no esta activo.",
            status_http=422,
        )

    ahora = datetime.now(UTC)
    expira = ahora + timedelta(hours=cfg.taam_codigo_emparejamiento_ttl_horas)
    codigo = generar_codigo_emparejamiento(cfg.taam_codigo_longitud).upper()

    pendiente = await repo_vinculos.obtener_pendiente_por_caso(caso_id)
    if pendiente is not None:
        await repo_vinculos.actualizar(
            pendiente,
            codigo_emparejamiento=codigo,
            codigo_expira_at=expira,
        )
    else:
        vinculado = await repo_vinculos.obtener_vinculado_por_caso(caso_id)
        if vinculado is not None:
            raise EmparejamientoError(
                codigo_error="caso_ya_vinculado",
                mensaje_telegram=(
                    "Este caso ya tiene un chat de Telegram vinculado. "
                    "Contacte al asistente si necesita cambiar el dispositivo."
                ),
                status_http=409,
            )
        await repo_vinculos.crear(
            caso_id=caso_id,
            telegram_chat_id=chat_id_placeholder(caso_id),
            codigo_emparejamiento=codigo,
            codigo_expira_at=expira,
            vinculado_at=None,
        )

    return CodigoGenerado(codigo=codigo, expira_at=expira, caso_id=caso_id)


async def emparejar_codigo(
    sesion: AsyncSession,
    *,
    codigo: str,
    telegram_chat_id: int,
) -> ResultadoEmparejar:
    repo_vinculos = RepositorioVinculosTelegram(sesion)
    repo_casos = RepositorioCasosPostoperatorio(sesion)

    codigo_norm = codigo.strip().upper()
    if not codigo_norm:
        raise EmparejamientoError(
            codigo_error="codigo_invalido",
            mensaje_telegram=(
                "Codigo invalido. Pida un codigo nuevo a su asistente quirurgico "
                "e intente de nuevo con /start CODIGO."
            ),
            status_http=400,
        )

    existente_chat = await repo_vinculos.obtener_vinculado_por_chat_id(telegram_chat_id)
    if existente_chat is not None:
        raise EmparejamientoError(
            codigo_error="chat_ya_vinculado",
            mensaje_telegram=(
                "Este chat de Telegram ya esta vinculado a un seguimiento activo. "
                "Si necesita ayuda, contacte a su equipo de salud."
            ),
            status_http=409,
        )

    pendiente = await repo_vinculos.obtener_pendiente_por_codigo(codigo_norm)
    if pendiente is None:
        raise EmparejamientoError(
            codigo_error="codigo_invalido",
            mensaje_telegram=(
                "Codigo invalido o ya utilizado. Solicite un codigo nuevo "
                "a su asistente e envie /start CODIGO."
            ),
            status_http=400,
        )

    ahora = datetime.now(UTC)
    expira = _en_utc(pendiente.codigo_expira_at)
    if expira is not None and expira < ahora:
        raise EmparejamientoError(
            codigo_error="codigo_expirado",
            mensaje_telegram=(
                "El codigo expiro. Pida un codigo nuevo a su asistente quirurgico "
                "e intente de nuevo con /start CODIGO."
            ),
            status_http=400,
        )

    caso = await repo_casos.obtener_por_id(pendiente.caso_id)
    if caso is None or caso.estado != "activo":
        raise EmparejamientoError(
            codigo_error="caso_no_activo",
            mensaje_telegram=(
                "El seguimiento ya no esta activo. Contacte a su asistente quirurgico."
            ),
            status_http=400,
        )

    await repo_vinculos.actualizar(
        pendiente,
        telegram_chat_id=telegram_chat_id,
        vinculado_at=ahora,
        limpiar_codigo=True,
    )

    nombre = caso.paciente_nombre.strip() or "paciente"
    return ResultadoEmparejar(
        caso_id=caso.id,
        vinculado_at=ahora,
        mensaje_confirmacion=(
            f"Hola, {nombre}. Su seguimiento postoperatorio quedo vinculado correctamente. "
            "Puede escribir sus dudas cuando lo necesite."
        ),
    )


async def caso_tiene_vinculo_telegram(
    sesion: AsyncSession,
    caso: CasoPostoperatorio,
) -> bool:
    repo = RepositorioVinculosTelegram(sesion)
    return (await repo.obtener_vinculado_por_caso(caso.id)) is not None


async def codigo_pendiente_activo(
    sesion: AsyncSession,
    caso_id: uuid.UUID,
) -> str | None:
    repo = RepositorioVinculosTelegram(sesion)
    pendiente = await repo.obtener_pendiente_por_caso(caso_id)
    if pendiente is None or not pendiente.codigo_emparejamiento:
        return None
    ahora = datetime.now(UTC)
    expira = _en_utc(pendiente.codigo_expira_at)
    if expira is not None and expira < ahora:
        return None
    return pendiente.codigo_emparejamiento
