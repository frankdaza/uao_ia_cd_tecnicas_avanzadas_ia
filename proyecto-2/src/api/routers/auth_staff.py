"""Login staff con JWT (TASK-105)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as estado_http
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth_staff import emitir_token_staff, verificar_contrasena
from src.api.esquemas_auth import StaffLoginCuerpo, StaffLoginRespuesta
from src.configuracion import Configuracion, obtener_configuracion
from src.persistencia.motor import obtener_sesion_db
from src.persistencia.repositorios.usuarios_staff import RepositorioUsuariosStaff

router = APIRouter(prefix="/auth/staff", tags=["auth-staff"])


def _cfg_auth_habilitada(cfg: Configuracion) -> None:
    if not (cfg.staff_jwt_secret or "").strip():
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Autenticacion staff deshabilitada: defina STAFF_JWT_SECRET en el servidor."
            ),
        )


@router.post("/login", response_model=StaffLoginRespuesta)
async def login_staff(
    cuerpo: StaffLoginCuerpo,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    cfg: Annotated[Configuracion, Depends(obtener_configuracion)],
) -> StaffLoginRespuesta:
    """Emite JWT HS256 tras validar email y contrasena (bcrypt)."""
    _cfg_auth_habilitada(cfg)
    repo = RepositorioUsuariosStaff(sesion)
    usuario = await repo.obtener_por_email(str(cuerpo.email))
    if usuario is None or not verificar_contrasena(
        cuerpo.password, usuario.hash_credencial
    ):
        raise HTTPException(
            status_code=estado_http.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
        )

    try:
        token, expira_en_seg = emitir_token_staff(usuario, cfg)
    except ValueError as exc:
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return StaffLoginRespuesta(
        access_token=token,
        expira_en_seg=expira_en_seg,
        rol=usuario.rol,
        nombre=usuario.nombre,
    )
