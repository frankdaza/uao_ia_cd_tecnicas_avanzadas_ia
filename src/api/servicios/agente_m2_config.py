"""Fusion de configuracion runtime del agente M2 (archivo, env y PostgreSQL)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.llm_deterministico_modulo2 import (
    CompositorDeterministicoModulo2E2e,
    RouterDeterministicoModulo2E2e,
)
from src.agentes.meta_prompt import (
    MetaPromptConfig,
    cargar_meta_prompt_config,
    meta_prompt_desde_dict,
)
from src.agentes.prompt_institucional import PROMPT_SISTEMA_DEFECTO
from src.agentes.reglas import coercionar_historial_dias_max
from src.agentes.runtime_agente import RuntimeAgenteBundle
from src.api._limites_rag import (
    asegurar_rango_parche_numerico,
    clamp_valor_admin_numerico,
)
from src.api.configuracion import Configuracion, obtener_configuracion
from src.persistencia.modelos import ConfigAdminM2
from src.persistencia.repositorios.config_admin_m2 import RepositorioConfigAdminM2

logger = logging.getLogger(__name__)
TEMPERATURA_ROUTER_DEFECTO_CODIGO: float = 0.0
TEMPERATURA_COMPOSITOR_DEFECTO_CODIGO: float = 0.2


def _resolver_ruta_meta_prompt(cfg: Configuracion) -> Path:
    raw = Path(cfg.router_meta_prompt_path)
    if raw.is_absolute():
        return raw
    raiz = Path(__file__).resolve().parents[3]
    return (raiz / raw).resolve()


class ConflictoVersionConfigAdminError(Exception):
    """La version enviada no coincide con la fila persistida (actualizacion concurrente)."""


class ServicioAgenteM2Config:
    """
    Lectura fusionada y persistencia de overrides del agente (singleton ``config_admin_m2``).

    Precedencia de datos efectivos (mayor a menor):
    columnas no nulas en PostgreSQL (``config_admin_m2``); archivo ``config/router_meta_prompt.json``;
    variables de entorno vía :class:`~src.api.configuracion.Configuracion` (p. ej. ``ROUTER_LLM_MODEL``,
    ``COMPOSITOR_LLM_MODEL``); temperaturas por defecto del codigo (0.0 router / 0.2 compositor) si no hay override.
    """

    def __init__(self, sesion: AsyncSession, cfg: Configuracion | None = None) -> None:
        self._sesion = sesion
        self._cfg = cfg or obtener_configuracion()
        self._repo = RepositorioConfigAdminM2(sesion)

    def _meta_desde_archivo(self) -> MetaPromptConfig:
        return cargar_meta_prompt_config(_resolver_ruta_meta_prompt(self._cfg))

    def fusionar_meta_prompt(self, fila: ConfigAdminM2 | None) -> MetaPromptConfig:
        if fila is not None and fila.meta_prompt_json is not None:
            raw = fila.meta_prompt_json
            if isinstance(raw, dict):
                return meta_prompt_desde_dict(raw)
        return self._meta_desde_archivo()

    def modelo_router_efectivo(self, fila: ConfigAdminM2 | None) -> str:
        if (
            fila is not None
            and fila.modelo_llm_router
            and str(fila.modelo_llm_router).strip()
        ):
            return str(fila.modelo_llm_router).strip()
        return self._cfg.router_llm_model.strip()

    def modelo_compositor_efectivo(self, fila: ConfigAdminM2 | None) -> str:
        if (
            fila is not None
            and fila.modelo_llm_compositor
            and str(fila.modelo_llm_compositor).strip()
        ):
            return str(fila.modelo_llm_compositor).strip()
        return (self._cfg.compositor_llm_model or self._cfg.router_llm_model).strip()

    def temperatura_router_efectiva(self, fila: ConfigAdminM2 | None) -> float:
        if fila is not None and fila.temperatura_router is not None:
            return float(fila.temperatura_router)
        return TEMPERATURA_ROUTER_DEFECTO_CODIGO

    def temperatura_compositor_efectiva(self, fila: ConfigAdminM2 | None) -> float:
        if fila is not None and fila.temperatura_compositor is not None:
            return float(fila.temperatura_compositor)
        return TEMPERATURA_COMPOSITOR_DEFECTO_CODIGO

    def top_p_router_efectivo(self, fila: ConfigAdminM2 | None) -> float | None:
        if fila is None or fila.top_p_router is None:
            return None
        return float(fila.top_p_router)

    def top_p_compositor_efectivo(self, fila: ConfigAdminM2 | None) -> float | None:
        if fila is None or fila.top_p_compositor is None:
            return None
        return float(fila.top_p_compositor)

    def kwargs_router(self, fila: ConfigAdminM2 | None) -> dict[str, Any]:
        if fila is None or fila.model_kwargs_router is None:
            return {}
        if isinstance(fila.model_kwargs_router, dict):
            return dict(fila.model_kwargs_router)
        return {}

    def kwargs_compositor(self, fila: ConfigAdminM2 | None) -> dict[str, Any]:
        if fila is None or fila.model_kwargs_compositor is None:
            return {}
        if isinstance(fila.model_kwargs_compositor, dict):
            return dict(fila.model_kwargs_compositor)
        return {}

    def prompt_institucional_efectivo(self, fila: ConfigAdminM2 | None) -> str:
        if (
            fila is not None
            and fila.prompt_institucional
            and str(fila.prompt_institucional).strip()
        ):
            return str(fila.prompt_institucional).strip()
        return PROMPT_SISTEMA_DEFECTO.rstrip()

    def _leer_columna_numerica_admin(
        self,
        campo: str,
        fila: ConfigAdminM2 | None,
        fallback: int | float,
    ) -> int | float:
        """Lee columna admin numerica aplicando clamp defensivo si el valor persistido esta fuera de rango."""
        if fila is None:
            return fallback
        raw = getattr(fila, campo, None)
        if raw is None:
            return fallback
        acotado, hubo_clamp = clamp_valor_admin_numerico(raw, campo)
        if hubo_clamp:
            logger.warning(
                "Parametro admin %s fuera de rango en base de datos: valor_original=%r valor_acotado=%r",
                campo,
                raw,
                acotado,
            )
        return acotado

    def rag_top_k_efectivo(self, fila: ConfigAdminM2 | None) -> int:
        return int(
            self._leer_columna_numerica_admin(
                "rag_top_k", fila, int(self._cfg.rag_top_k)
            )
        )

    def rag_score_minimo_efectivo(self, fila: ConfigAdminM2 | None) -> float:
        return float(
            self._leer_columna_numerica_admin(
                "rag_score_minimo", fila, float(self._cfg.rag_score_minimo)
            )
        )

    def rag_top_k_inicial_efectivo(self, fila: ConfigAdminM2 | None) -> int:
        return int(
            self._leer_columna_numerica_admin(
                "rag_top_k_inicial", fila, int(self._cfg.rag_top_k_inicial)
            )
        )

    def rag_mmr_habilitado_efectivo(self, fila: ConfigAdminM2 | None) -> bool:
        if fila is not None and fila.rag_mmr_habilitado is not None:
            return bool(fila.rag_mmr_habilitado)
        return bool(self._cfg.rag_mmr_habilitado)

    def rag_mmr_lambda_efectivo(self, fila: ConfigAdminM2 | None) -> float:
        return float(
            self._leer_columna_numerica_admin(
                "rag_mmr_lambda", fila, float(self._cfg.rag_mmr_lambda)
            )
        )

    def rag_reranker_habilitado_efectivo(self, fila: ConfigAdminM2 | None) -> bool:
        if fila is not None and fila.rag_reranker_habilitado is not None:
            return bool(fila.rag_reranker_habilitado)
        return bool(self._cfg.rag_reranker_habilitado)

    def rag_reranker_modelo_efectivo(self, fila: ConfigAdminM2 | None) -> str:
        if (
            fila is not None
            and fila.rag_reranker_modelo
            and str(fila.rag_reranker_modelo).strip()
        ):
            return str(fila.rag_reranker_modelo).strip()
        return str(self._cfg.rag_reranker_modelo).strip()

    def rag_reranker_top_n_entrada_efectivo(self, fila: ConfigAdminM2 | None) -> int:
        return int(
            self._leer_columna_numerica_admin(
                "rag_reranker_top_n_entrada",
                fila,
                int(self._cfg.rag_reranker_top_n_entrada),
            )
        )

    def rag_reranker_batch_size_efectivo(self, fila: ConfigAdminM2 | None) -> int:
        return int(
            self._leer_columna_numerica_admin(
                "rag_reranker_batch_size",
                fila,
                int(self._cfg.rag_reranker_batch_size),
            )
        )

    def historial_turnos_max_efectivo(self, fila: ConfigAdminM2 | None) -> int:
        return int(
            self._leer_columna_numerica_admin(
                "historial_turnos_max",
                fila,
                int(self._cfg.historial_turnos_max),
            )
        )

    def historial_dias_max_efectivo(self, fila: ConfigAdminM2 | None) -> int:
        return coercionar_historial_dias_max(
            int(
                self._leer_columna_numerica_admin(
                    "historial_dias_max",
                    fila,
                    int(self._cfg.historial_dias_max),
                )
            )
        )

    async def obtener_fila(self) -> ConfigAdminM2 | None:
        return await self._repo.obtener()

    def _chat_openai_router(self, fila: ConfigAdminM2 | None) -> ChatOpenAI:
        kwargs_llm: dict[str, Any] = {
            "model": self.modelo_router_efectivo(fila),
            "api_key": self._cfg.openai_api_key,
            "temperature": self.temperatura_router_efectiva(fila),
            "model_kwargs": self.kwargs_router(fila),
        }
        tp = self.top_p_router_efectivo(fila)
        if tp is not None:
            kwargs_llm["top_p"] = tp
        if self._cfg.openai_base_url and str(self._cfg.openai_base_url).strip():
            kwargs_llm["base_url"] = str(self._cfg.openai_base_url).strip()
        kwargs_llm["timeout"] = self._cfg.openai_timeout_segundos
        if self._cfg.openai_max_completion_tokens is not None:
            kwargs_llm["max_completion_tokens"] = self._cfg.openai_max_completion_tokens
        return ChatOpenAI(**kwargs_llm)

    def _chat_openai_compositor(self, fila: ConfigAdminM2 | None) -> ChatOpenAI:
        kwargs_llm: dict[str, Any] = {
            "model": self.modelo_compositor_efectivo(fila),
            "api_key": self._cfg.openai_api_key,
            "temperature": self.temperatura_compositor_efectiva(fila),
            "model_kwargs": self.kwargs_compositor(fila),
        }
        tp = self.top_p_compositor_efectivo(fila)
        if tp is not None:
            kwargs_llm["top_p"] = tp
        if self._cfg.openai_base_url and str(self._cfg.openai_base_url).strip():
            kwargs_llm["base_url"] = str(self._cfg.openai_base_url).strip()
        kwargs_llm["timeout"] = self._cfg.openai_timeout_segundos
        if self._cfg.openai_max_completion_tokens is not None:
            kwargs_llm["max_completion_tokens"] = self._cfg.openai_max_completion_tokens
        return ChatOpenAI(**kwargs_llm)

    async def construir_bundle_tiempo_ejecucion(self) -> RuntimeAgenteBundle:
        """
        Snapshot para una invocacion del grafo (p. ej. un ``POST /api/agente/stream``).

        Con ``MOCK_LLM=1`` se ignoran temperaturas/modelos OpenAI y se usan LLMs deterministicos;
        el meta-prompt y el texto institucional siguen pudiendo venir de PostgreSQL si existen.
        """
        fila = await self.obtener_fila()
        meta = self.fusionar_meta_prompt(fila)
        prompt_inst = self.prompt_institucional_efectivo(fila)
        etiqueta = self.modelo_compositor_efectivo(fila)

        if self._cfg.mock_llm:
            return RuntimeAgenteBundle(
                llm_router=RouterDeterministicoModulo2E2e(),
                llm_compositor=CompositorDeterministicoModulo2E2e(),
                meta_prompt=meta,
                prompt_institucional=prompt_inst,
                etiqueta_modelo_compositor="mock_llm",
                rag_top_k=self.rag_top_k_efectivo(fila),
                rag_score_minimo=self.rag_score_minimo_efectivo(fila),
                historial_turnos_max=self.historial_turnos_max_efectivo(fila),
                historial_dias_max=self.historial_dias_max_efectivo(fila),
                rag_top_k_inicial=self.rag_top_k_inicial_efectivo(fila),
                rag_mmr_habilitado=self.rag_mmr_habilitado_efectivo(fila),
                rag_mmr_lambda=self.rag_mmr_lambda_efectivo(fila),
                rag_reranker_habilitado=self.rag_reranker_habilitado_efectivo(fila),
                rag_reranker_modelo=self.rag_reranker_modelo_efectivo(fila),
                rag_reranker_top_n_entrada=self.rag_reranker_top_n_entrada_efectivo(
                    fila
                ),
                rag_reranker_batch_size=self.rag_reranker_batch_size_efectivo(fila),
            )

        if not (self._cfg.openai_api_key and str(self._cfg.openai_api_key).strip()):
            msg = "Falta OPENAI_API_KEY para inicializar modelos chat del agente."
            raise ValueError(msg)

        return RuntimeAgenteBundle(
            llm_router=self._chat_openai_router(fila),
            llm_compositor=self._chat_openai_compositor(fila),
            meta_prompt=meta,
            prompt_institucional=prompt_inst,
            etiqueta_modelo_compositor=etiqueta,
            rag_top_k=self.rag_top_k_efectivo(fila),
            rag_score_minimo=self.rag_score_minimo_efectivo(fila),
            historial_turnos_max=self.historial_turnos_max_efectivo(fila),
            historial_dias_max=self.historial_dias_max_efectivo(fila),
            rag_top_k_inicial=self.rag_top_k_inicial_efectivo(fila),
            rag_mmr_habilitado=self.rag_mmr_habilitado_efectivo(fila),
            rag_mmr_lambda=self.rag_mmr_lambda_efectivo(fila),
            rag_reranker_habilitado=self.rag_reranker_habilitado_efectivo(fila),
            rag_reranker_modelo=self.rag_reranker_modelo_efectivo(fila),
            rag_reranker_top_n_entrada=self.rag_reranker_top_n_entrada_efectivo(fila),
            rag_reranker_batch_size=self.rag_reranker_batch_size_efectivo(fila),
        )

    async def aplicar_parche(
        self,
        *,
        version_esperada: int,
        modelo_llm_router: str | None = None,
        modelo_llm_compositor: str | None = None,
        temperatura_router: float | None = None,
        temperatura_compositor: float | None = None,
        top_p_router: float | None = None,
        top_p_compositor: float | None = None,
        model_kwargs_router: dict[str, Any] | None = None,
        model_kwargs_compositor: dict[str, Any] | None = None,
        meta_prompt: dict[str, Any] | None = None,
        prompt_institucional: str | None = None,
        rag_top_k: int | None = None,
        rag_score_minimo: float | None = None,
        rag_top_k_inicial: int | None = None,
        rag_mmr_habilitado: bool | None = None,
        rag_mmr_lambda: float | None = None,
        rag_reranker_habilitado: bool | None = None,
        rag_reranker_modelo: str | None = None,
        rag_reranker_top_n_entrada: int | None = None,
        rag_reranker_batch_size: int | None = None,
        historial_turnos_max: int | None = None,
        historial_dias_max: int | None = None,
    ) -> ConfigAdminM2:
        """Persiste cambios parciales con control optimista de ``version``."""
        fila_bloqueada = await self._repo.obtener_para_actualizar()
        version_db = int(fila_bloqueada.version) if fila_bloqueada is not None else 0
        if version_esperada != version_db:
            raise ConflictoVersionConfigAdminError(
                f"Version esperada {version_esperada} distinta de la persistida {version_db}."
            )

        if fila_bloqueada is None:
            nueva = ConfigAdminM2(
                id=1,
                version=1,
            )
            self._repo.agregar_inicial(nueva)
            fila = nueva
        else:
            fila = fila_bloqueada
            fila.version = int(fila.version) + 1

        if modelo_llm_router is not None:
            mr = modelo_llm_router.strip()
            if not mr:
                msg = "modelo_llm_router no puede quedar vacio al persistir."
                raise ValueError(msg)
            fila.modelo_llm_router = mr
        if modelo_llm_compositor is not None:
            mc = modelo_llm_compositor.strip()
            if not mc:
                msg = "modelo_llm_compositor no puede quedar vacio al persistir."
                raise ValueError(msg)
            fila.modelo_llm_compositor = mc
        if temperatura_router is not None:
            fila.temperatura_router = float(temperatura_router)
        if temperatura_compositor is not None:
            fila.temperatura_compositor = float(temperatura_compositor)
        if top_p_router is not None:
            fila.top_p_router = float(top_p_router)
        if top_p_compositor is not None:
            fila.top_p_compositor = float(top_p_compositor)
        if model_kwargs_router is not None:
            fila.model_kwargs_router = model_kwargs_router or None
        if model_kwargs_compositor is not None:
            fila.model_kwargs_compositor = model_kwargs_compositor or None
        if meta_prompt is not None:
            try:
                meta_prompt_desde_dict(dict(meta_prompt))
            except (ValidationError, TypeError, ValueError) as exc:
                msg = f"Meta-prompt invalido: {exc}"
                raise ValueError(msg) from exc
            fila.meta_prompt_json = dict(meta_prompt)
        if prompt_institucional is not None:
            texto = prompt_institucional.strip()
            if len(texto) < 80:
                msg = "El prompt institucional debe tener al menos 80 caracteres."
                raise ValueError(msg)
            fila.prompt_institucional = texto
        if rag_top_k is not None:
            asegurar_rango_parche_numerico("rag_top_k", int(rag_top_k))
            fila.rag_top_k = int(rag_top_k)
        if rag_score_minimo is not None:
            asegurar_rango_parche_numerico("rag_score_minimo", float(rag_score_minimo))
            fila.rag_score_minimo = float(rag_score_minimo)
        if rag_top_k_inicial is not None:
            asegurar_rango_parche_numerico("rag_top_k_inicial", int(rag_top_k_inicial))
            fila.rag_top_k_inicial = int(rag_top_k_inicial)
        if rag_mmr_habilitado is not None:
            fila.rag_mmr_habilitado = bool(rag_mmr_habilitado)
        if rag_mmr_lambda is not None:
            asegurar_rango_parche_numerico("rag_mmr_lambda", float(rag_mmr_lambda))
            fila.rag_mmr_lambda = float(rag_mmr_lambda)
        if rag_reranker_habilitado is not None:
            fila.rag_reranker_habilitado = bool(rag_reranker_habilitado)
        if rag_reranker_modelo is not None:
            rm = str(rag_reranker_modelo).strip()
            if len(rm) > 256:
                msg = "rag_reranker_modelo admite como maximo 256 caracteres."
                raise ValueError(msg)
            if not rm:
                msg = "rag_reranker_modelo no puede quedar vacio al persistir."
                raise ValueError(msg)
            fila.rag_reranker_modelo = rm
        if rag_reranker_top_n_entrada is not None:
            asegurar_rango_parche_numerico(
                "rag_reranker_top_n_entrada", int(rag_reranker_top_n_entrada)
            )
            fila.rag_reranker_top_n_entrada = int(rag_reranker_top_n_entrada)
        if rag_reranker_batch_size is not None:
            asegurar_rango_parche_numerico(
                "rag_reranker_batch_size", int(rag_reranker_batch_size)
            )
            fila.rag_reranker_batch_size = int(rag_reranker_batch_size)
        if historial_turnos_max is not None:
            asegurar_rango_parche_numerico(
                "historial_turnos_max", int(historial_turnos_max)
            )
            fila.historial_turnos_max = int(historial_turnos_max)
        if historial_dias_max is not None:
            asegurar_rango_parche_numerico(
                "historial_dias_max", int(historial_dias_max)
            )
            fila.historial_dias_max = int(historial_dias_max)

        await self._sesion.flush()
        return fila


__all__ = [
    "ConflictoVersionConfigAdminError",
    "ServicioAgenteM2Config",
    "TEMPERATURA_COMPOSITOR_DEFECTO_CODIGO",
    "TEMPERATURA_ROUTER_DEFECTO_CODIGO",
]
