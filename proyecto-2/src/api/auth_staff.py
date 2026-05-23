"""Utilidades de hash y JWT para autenticacion staff (TASK-105)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from src.configuracion import Configuracion
from src.persistencia.modelos import ROLES_STAFF, UsuarioStaff


@dataclass(frozen=True, slots=True)
class ClaimsStaffJwt:
    """Claims decodificados del access token staff."""

    usuario_id: uuid.UUID
    rol: str
    nombre: str


def hash_contrasena(contrasena: str) -> str:
    """Genera hash bcrypt para almacenar en ``usuarios_staff.hash_credencial``."""
    sal = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena.encode("utf-8"), sal).decode("utf-8")


def verificar_contrasena(contrasena: str, hash_credencial: str | None) -> bool:
    """Compara contrasena en texto plano con hash bcrypt almacenado."""
    if not hash_credencial or not hash_credencial.strip():
        return False
    try:
        return bcrypt.checkpw(
            contrasena.encode("utf-8"),
            hash_credencial.encode("utf-8"),
        )
    except ValueError:
        return False


def _asegurar_secreto_jwt(cfg: Configuracion) -> str:
    secreto = (cfg.staff_jwt_secret or "").strip()
    if not secreto:
        raise ValueError("STAFF_JWT_SECRET no configurado")
    return secreto


def emitir_token_staff(usuario: UsuarioStaff, cfg: Configuracion) -> tuple[str, int]:
    """
    Firma un JWT HS256 y devuelve ``(token, expira_en_seg)``.

    Raises:
        ValueError: si falta ``STAFF_JWT_SECRET``.
    """
    secreto = _asegurar_secreto_jwt(cfg)
    ahora = datetime.now(UTC)
    expira_en_seg = int(cfg.staff_jwt_expire_horas * 3600)
    expira = ahora + timedelta(seconds=expira_en_seg)
    payload = {
        "sub": str(usuario.id),
        "rol": usuario.rol,
        "nombre": usuario.nombre,
        "iat": int(ahora.timestamp()),
        "exp": int(expira.timestamp()),
    }
    token = jwt.encode(payload, secreto, algorithm="HS256")
    return token, expira_en_seg


def decodificar_token_staff(token: str, cfg: Configuracion) -> ClaimsStaffJwt:
    """
    Valida firma y expiracion del JWT staff.

    Raises:
        jwt.InvalidTokenError: token invalido o expirado.
        ValueError: claims incompletos o rol desconocido.
    """
    secreto = _asegurar_secreto_jwt(cfg)
    payload = jwt.decode(
        token,
        secreto,
        algorithms=["HS256"],
        options={"require": ["sub", "rol", "nombre", "exp"]},
    )
    try:
        usuario_id = uuid.UUID(str(payload["sub"]))
    except (ValueError, TypeError) as exc:
        raise ValueError("sub invalido en JWT") from exc

    rol = str(payload.get("rol", "")).strip()
    if rol not in ROLES_STAFF:
        raise ValueError("rol invalido en JWT")

    nombre = str(payload.get("nombre", "")).strip()
    if not nombre:
        raise ValueError("nombre ausente en JWT")

    return ClaimsStaffJwt(usuario_id=usuario_id, rol=rol, nombre=nombre)
