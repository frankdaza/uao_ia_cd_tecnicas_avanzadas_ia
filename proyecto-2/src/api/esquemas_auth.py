"""Esquemas Pydantic para autenticacion staff."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class StaffLoginCuerpo(BaseModel):
    """Credenciales de acceso al panel staff."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=256)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "asistente@demo.taam",
                    "password": "cambiar-demo-asistente",
                }
            ]
        }
    }


class StaffLoginRespuesta(BaseModel):
    """Token JWT de corta vida para rutas staff y admin (rol admin)."""

    access_token: str
    token_type: str = "bearer"
    expira_en_seg: int = Field(ge=1)
    rol: str
    nombre: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expira_en_seg": 28800,
                    "rol": "asistente",
                    "nombre": "Asistente Demo",
                }
            ]
        }
    }
