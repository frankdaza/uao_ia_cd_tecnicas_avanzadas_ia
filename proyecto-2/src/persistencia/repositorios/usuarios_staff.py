"""Repositorio de ``usuarios_staff``."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth_staff import hash_contrasena
from src.persistencia.modelos import UsuarioStaff


class RepositorioUsuariosStaff:
    """CRUD minimo sobre usuarios del panel staff."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def obtener_por_id(self, usuario_id: uuid.UUID) -> UsuarioStaff | None:
        return await self._sesion.get(UsuarioStaff, usuario_id)

    async def obtener_por_email(self, email: str) -> UsuarioStaff | None:
        email_norm = email.strip().lower()
        stmt = select(UsuarioStaff).where(UsuarioStaff.email == email_norm)
        resultado = await self._sesion.execute(stmt)
        return resultado.scalar_one_or_none()

    async def crear_o_actualizar_credencial(
        self,
        *,
        email: str,
        nombre: str,
        rol: str,
        contrasena_plana: str,
    ) -> UsuarioStaff:
        """Crea usuario demo o actualiza hash si ya existe (semilla idempotente)."""
        email_norm = email.strip().lower()
        fila = await self.obtener_por_email(email_norm)
        hash_nuevo = hash_contrasena(contrasena_plana)
        if fila is None:
            fila = UsuarioStaff(
                email=email_norm,
                nombre=nombre.strip(),
                rol=rol,
                hash_credencial=hash_nuevo,
            )
            self._sesion.add(fila)
        else:
            fila.nombre = nombre.strip()
            fila.rol = rol
            fila.hash_credencial = hash_nuevo
        await self._sesion.flush()
        return fila
