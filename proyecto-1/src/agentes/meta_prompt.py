"""
Carga y validacion del meta-prompt del router (JSON bajo ``config/``).

La configuracion se cachea en memoria por ``mtime`` del archivo para permitir
ediciones en caliente sin reiniciar el proceso.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from src.rutas_workspace import resolver_ruta_proyecto

_RUTA_JSON_DEFECTO = resolver_ruta_proyecto("config/router_meta_prompt.json")

# Texto canonico alineado con ``src/laboratorio/qa_legacy/prompt.py`` (politica Lili).
_TEXTO_SIN_CONTEXTO_CANONICO = "No tengo información suficiente"

_NOMBRES_HERRAMIENTAS_REQUERIDAS: frozenset[str] = frozenset(
    {"faq_estructurada", "rag_denso", "listar_estructurado"}
)


class ArchivoMetaPromptAusenteError(FileNotFoundError):
    """No existe o no es legible ``router_meta_prompt.json`` en la ruta esperada."""


class MetaPromptHerramienta(BaseModel):
    """Definicion pedagogica de una tool expuesta al router (no sustituye el binding real)."""

    name: Literal["faq_estructurada", "rag_denso", "listar_estructurado"]
    description: str = Field(min_length=1)
    when_to_use: str = Field(min_length=1)
    ejemplos: list[str] = Field(default_factory=list)


class MetaPromptConfig(BaseModel):
    """Schema del archivo ``config/router_meta_prompt.json`` (version 1)."""

    version: Literal[1] = Field(
        description="Version del schema; solo se admite 1 por ahora."
    )
    modelo_router: str = Field(min_length=1)
    system_prompt: str = Field(
        min_length=80,
        description="Instrucciones al LLM del router; debe orientar a tool-calls, no texto libre.",
    )
    herramientas: list[MetaPromptHerramienta]
    reglas_decision: list[str] = Field(min_length=1)
    respuesta_sin_contexto: str = Field(min_length=1)
    saludo_template: str = Field(
        min_length=1,
        description="Plantilla de saludo; debe incluir el placeholder {nombre}.",
    )

    @model_validator(mode="after")
    def validar_herramientas_y_politicas(self) -> Self:
        nombres = {h.name for h in self.herramientas}
        if nombres != _NOMBRES_HERRAMIENTAS_REQUERIDAS:
            raise ValueError(
                "``herramientas`` debe incluir exactamente una entrada por cada nombre: "
                f"{sorted(_NOMBRES_HERRAMIENTAS_REQUERIDAS)} (recibido: {sorted(nombres)})."
            )
        if self.respuesta_sin_contexto.strip() != _TEXTO_SIN_CONTEXTO_CANONICO:
            raise ValueError(
                "``respuesta_sin_contexto`` debe coincidir con la politica del corpus Lili: "
                f"{_TEXTO_SIN_CONTEXTO_CANONICO!r}."
            )
        if "{nombre}" not in self.saludo_template:
            raise ValueError(
                "``saludo_template`` debe documentar el placeholder soportado ``{nombre}`` "
                "(cadena literal presente en la plantilla)."
            )
        for i, regla in enumerate(self.reglas_decision):
            if not regla.strip():
                raise ValueError(
                    f"``reglas_decision[{i}]`` no puede ser vacia ni solo espacios."
                )
        return self


_cache_por_ruta: dict[str, tuple[int, MetaPromptConfig]] = {}


def limpiar_cache_meta_prompt() -> None:
    """Vacía la cache en memoria (util en tests o tras reemplazar el archivo por otra ruta)."""
    _cache_por_ruta.clear()


def _clave_cache(ruta: Path) -> str:
    return str(ruta.resolve())


def cargar_meta_prompt_config(
    ruta: Path | None = None,
) -> MetaPromptConfig:
    """
    Lee y valida el JSON del meta-prompt, con cache invalidada por ``mtime_ns``.

    Parameters
    ----------
    ruta:
        Ruta al JSON; por defecto ``config/router_meta_prompt.json`` en la raiz del repo.
    """
    path = (ruta or _RUTA_JSON_DEFECTO).resolve()
    if not path.is_file():
        raise ArchivoMetaPromptAusenteError(
            f"No se encontro el archivo de meta-prompt del router: {path}"
        )
    clave = _clave_cache(path)
    mtime_ns = path.stat().st_mtime_ns
    previo = _cache_por_ruta.get(clave)
    if previo is not None and previo[0] == mtime_ns:
        return previo[1]
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalido en {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"El JSON en {path} debe ser un objeto en la raiz.")
    config = MetaPromptConfig.model_validate(payload)
    _cache_por_ruta[clave] = (mtime_ns, config)
    return config


def meta_prompt_desde_dict(payload: dict[str, object]) -> MetaPromptConfig:
    """
    Valida un diccionario como :class:`MetaPromptConfig` (misma regla que el JSON en disco).

    Parameters
    ----------
    payload:
        Objeto raiz equivalente al archivo ``router_meta_prompt.json``.
    """
    if not isinstance(payload, dict):
        msg = "El meta-prompt debe ser un objeto JSON en la raiz."
        raise TypeError(msg)
    return MetaPromptConfig.model_validate(payload)


def obtener_ruta_meta_prompt_defecto() -> Path:
    """Ruta canónica versionada bajo ``config/router_meta_prompt.json``."""
    return _RUTA_JSON_DEFECTO
