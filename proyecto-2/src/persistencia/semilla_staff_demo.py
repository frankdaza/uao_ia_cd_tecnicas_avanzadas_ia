"""Semilla idempotente de usuarios staff demo (TASK-105)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.configuracion import Configuracion
from src.persistencia.repositorios.usuarios_staff import RepositorioUsuariosStaff

USUARIOS_DEMO = (
    ("asistente@demo.taam", "Asistente Demo", "asistente", "staff_demo_asistente_password"),
    ("clinico@demo.taam", "Clinico Demo", "clinico", "staff_demo_clinico_password"),
    ("admin@demo.taam", "Admin Demo", "admin", "staff_demo_admin_password"),
)


async def sembrar_usuarios_staff_demo(
    sesion: AsyncSession,
    cfg: Configuracion,
) -> list[str]:
    """
    Crea o actualiza los tres usuarios demo.

    Returns:
        Lista de emails sembrados.
    """
    repo = RepositorioUsuariosStaff(sesion)
    emails: list[str] = []
    for email, nombre, rol, attr_password in USUARIOS_DEMO:
        contrasena = getattr(cfg, attr_password)
        await repo.crear_o_actualizar_credencial(
            email=email,
            nombre=nombre,
            rol=rol,
            contrasena_plana=contrasena,
        )
        emails.append(email.strip().lower())
    return emails
