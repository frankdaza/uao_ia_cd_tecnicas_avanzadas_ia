"""Guardrail de alcance: solo consultas de seguimiento postoperatorio (Lili Bot)."""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.configuracion import Configuracion, obtener_configuracion

logger = logging.getLogger(__name__)

MENSAJE_FUERA_DE_ALCANCE = (
    "Solo puedo orientarte sobre tu seguimiento postoperatorio y los cuidados de tu "
    "procedimiento. Si tienes dudas sobre tu recuperacion, cuentame y con gusto te ayudo."
)

# Saludos breves permitidos (redirige el agente al postoperatorio).
_SALUDOS_CORTOS: frozenset[str] = frozenset(
    {
        "hola",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "gracias",
        "muchas gracias",
        "ok",
        "vale",
        "listo",
        "entendido",
        "buen dia",
    }
)

# Temas claramente ajenos al seguimiento postoperatorio.
_PATRONES_FUERA: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bpython\b"),
    re.compile(r"\bjavascript\b"),
    re.compile(r"\bjava\b(?!script)"),
    re.compile(r"\btypescript\b"),
    re.compile(r"\bprogramar\b"),
    re.compile(r"\bprogramacion\b"),
    re.compile(r"\bcodigo\b"),
    re.compile(r"\bhello\s+world\b"),
    re.compile(r"\bhola\s+mundo\b"),
    re.compile(r"\bhtml\b"),
    re.compile(r"\bcss\b"),
    re.compile(r"\bsql\b"),
    re.compile(r"\breact\b"),
    re.compile(r"\bnode\.?js\b"),
    re.compile(r"\bdolar\b"),
    re.compile(r"\beuro\b"),
    re.compile(r"\bcotizacion\b"),
    re.compile(r"\bbitcoin\b"),
    re.compile(r"\bcrypto\b"),
    re.compile(r"\bfutbol\b"),
    re.compile(r"\bbeisbol\b"),
    re.compile(r"\bpartido\b"),
    re.compile(r"\bnoticias\b"),
    re.compile(r"\bpolitica\b"),
    re.compile(r"\belecciones\b"),
    re.compile(r"\btarea\s+de\s+matematic"),
    re.compile(r"\bexamen\s+de\s+"),
    re.compile(r"\breceta\s+de\s+(?!medic|antibiot|analges)"),
    re.compile(r"\bcomo\s+cocinar\b"),
    re.compile(r"\bclima\b"),
    re.compile(r"\bpelicula\b"),
    re.compile(r"\bnetflix\b"),
)

# Indicios de consulta clinica / postoperatoria.
_PATRONES_DENTRO: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bpostoperator"),
    re.compile(r"\bposoperator"),
    re.compile(r"\bcirugi"),
    re.compile(r"\boperacion\b"),
    re.compile(r"\bprocedimiento\b"),
    re.compile(r"\bherida\b"),
    re.compile(r"\bcicatriz"),
    re.compile(r"\bapendicect"),
    re.compile(r"\bcolecistect"),
    re.compile(r"\bfiebre\b"),
    re.compile(r"\bdolor\b"),
    re.compile(r"\bsangrado\b"),
    re.compile(r"\bhemorrag"),
    re.compile(r"\bnausea\b"),
    re.compile(r"\bvomito\b"),
    re.compile(r"\bmedic"),
    re.compile(r"\bfarmaco\b"),
    re.compile(r"\bpastilla\b"),
    re.compile(r"\bantibiot"),
    re.compile(r"\banalges"),
    re.compile(r"\bcaminar\b"),
    re.compile(r"\bdeambul"),
    re.compile(r"\bejercicio\b"),
    re.compile(r"\bdieta\b"),
    re.compile(r"\baliment"),
    re.compile(r"\bbaño\b"),
    re.compile(r"\bducha\b"),
    re.compile(r"\bcuracion\b"),
    re.compile(r"\bvendaje\b"),
    re.compile(r"\brecuperacion\b"),
    re.compile(r"\balta\b"),
    re.compile(r"\bcita\b"),
    re.compile(r"\bcontrol\b"),
    re.compile(r"\burgencia"),
    re.compile(r"\bemergencia"),
    re.compile(r"\brespir"),
    re.compile(r"\binflam"),
    re.compile(r"\binfeccion\b"),
    re.compile(r"\bprotocolo\b"),
    re.compile(r"\btriage\b"),
    re.compile(r"\bsintoma"),
    re.compile(r"\bsenal(es)?\s+de\s+alarma\b"),
    re.compile(r"\bemparej"),
    re.compile(r"\bcodigo\b"),
    re.compile(r"\b/start\b"),
)


class ClasificacionAlcanceLlm(BaseModel):
    """Salida estructurada del clasificador de alcance."""

    en_alcance: bool = Field(
        description=(
            "True si la consulta es sobre seguimiento postoperatorio, recuperacion, "
            "sintomas relacionados con la cirugia o cuidados del procedimiento."
        )
    )
    razon_corta: str = Field(
        max_length=120,
        description="Motivo breve de la clasificacion.",
    )


@dataclass(frozen=True)
class ResultadoAlcance:
    """Resultado de evaluar si el mensaje del paciente esta en dominio TAAM."""

    en_alcance: bool
    motivo: str


def _normalizar_texto(texto: str) -> str:
    t = texto.strip().lower()
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _coincide_alguno(texto: str, patrones: tuple[re.Pattern[str], ...]) -> bool:
    return any(p.search(texto) for p in patrones)


def _es_saludo_corto(texto_norm: str) -> bool:
    limpio = re.sub(r"[^\w\s]", " ", texto_norm)
    limpio = re.sub(r"\s+", " ", limpio).strip()
    if not limpio or len(limpio) > 40:
        return False
    return limpio in _SALUDOS_CORTOS


def _evaluar_heuristica(mensaje: str) -> ResultadoAlcance | None:
    """
    Clasificacion rapida sin LLM.

    Returns:
        ResultadoAlcance si la heuristica decide; None si debe pasar al clasificador LLM.
    """
    texto = _normalizar_texto(mensaje)
    if not texto:
        return None

    if _es_saludo_corto(texto):
        return ResultadoAlcance(en_alcance=True, motivo="saludo_corto")

    fuera = _coincide_alguno(texto, _PATRONES_FUERA)
    dentro = _coincide_alguno(texto, _PATRONES_DENTRO)

    if fuera and not dentro:
        return ResultadoAlcance(en_alcance=False, motivo="heuristica_fuera")
    if dentro and not fuera:
        return ResultadoAlcance(en_alcance=True, motivo="heuristica_dentro")
    return None


_PROMPT_CLASIFICADOR = """\
Eres un clasificador de alcance para un bot de seguimiento postoperatorio hospitalario.
Responde en_alcance=true solo si el mensaje del paciente trata sobre:
- recuperacion o cuidados despues de una cirugia,
- sintomas o signos relacionados con el postoperatorio,
- medicacion, herida, dieta, actividad, citas de control o protocolo de su procedimiento,
- emparejamiento con el bot o codigo entregado por el equipo,
- saludos breves o agradecimientos orientados a continuar el seguimiento.

Responde en_alcance=false para temas ajenos: programacion, finanzas, deportes, noticias,
tareas escolares no medicas, entretenimiento, cocina general, etc.
"""


@lru_cache(maxsize=1)
def _modelo_clasificador(modelo: str, api_key: str) -> object:
    kwargs: dict[str, object] = {"temperature": 0}
    if api_key.strip():
        kwargs["api_key"] = api_key
    return init_chat_model(modelo, **kwargs)


async def _clasificar_con_llm(mensaje: str, cfg: Configuracion) -> ResultadoAlcance:
    modelo = cfg.agente_guardrail_modelo.strip() or cfg.agente_modelo
    llm = _modelo_clasificador(modelo, cfg.openai_api_key)
    estructurado = llm.with_structured_output(ClasificacionAlcanceLlm)  # type: ignore[attr-defined]
    salida: ClasificacionAlcanceLlm = await estructurado.ainvoke(  # type: ignore[union-attr]
        [
            SystemMessage(content=_PROMPT_CLASIFICADOR),
            HumanMessage(content=mensaje.strip()),
        ]
    )
    motivo = f"llm:{salida.razon_corta[:80]}"
    return ResultadoAlcance(en_alcance=salida.en_alcance, motivo=motivo)


async def evaluar_alcance_consulta(
    mensaje: str,
    cfg: Configuracion | None = None,
) -> ResultadoAlcance:
    """
    Determina si el mensaje del paciente pertenece al dominio postoperatorio TAAM.

    Flujo: heuristica -> (opcional) clasificador LLM en casos dudosos.
    """
    conf = cfg or obtener_configuracion()
    if not conf.agente_guardrails_habilitado:
        return ResultadoAlcance(en_alcance=True, motivo="guardrails_desactivados")

    heuristica = _evaluar_heuristica(mensaje)
    if heuristica is not None:
        return heuristica

    if not conf.openai_api_key.strip():
        logger.warning(
            "guardrail_dudoso_sin_openai: se permite el turno al agente (sin clasificador LLM)"
        )
        return ResultadoAlcance(en_alcance=True, motivo="dudoso_sin_api_clasificador")

    try:
        return await _clasificar_con_llm(mensaje, conf)
    except Exception:
        logger.exception("guardrail_clasificador_llm_fallo: se permite el turno al agente")
        return ResultadoAlcance(en_alcance=True, motivo="llm_clasificador_error")
