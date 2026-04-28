"""Cliente para la API oficial de OpenAI (chat completions), alineado al flujo del pipeline Q&A."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

# Lista curada de exactamente cinco identificadores válidos para el parámetro ``model``
# en ``chat.completions``. Verificar disponibilidad y deprecaciones antes de producción en:
# https://platform.openai.com/docs/models
MODELO_OPENAI_GPT_4O: str = "gpt-4o"
MODELO_OPENAI_GPT_4O_MINI: str = "gpt-4o-mini"
MODELO_OPENAI_GPT_4_TURBO: str = "gpt-4-turbo"
MODELO_OPENAI_CHATGPT_4O_LATEST: str = "chatgpt-4o-latest"
MODELO_OPENAI_GPT_35_TURBO: str = "gpt-3.5-turbo"

MODELOS_OPENAI_SOPORTADOS: tuple[str, ...] = (
    MODELO_OPENAI_GPT_4O,
    MODELO_OPENAI_GPT_4O_MINI,
    MODELO_OPENAI_GPT_4_TURBO,
    MODELO_OPENAI_CHATGPT_4O_LATEST,
    MODELO_OPENAI_GPT_35_TURBO,
)

# Intentos ante HTTP 429 (rate limit): create + backoff corto.
_MAX_INTENTOS_RATE_LIMIT: int = 3


def _segundos_retry_after(exc: RateLimitError) -> float | None:
    """Lee ``Retry-After`` si la respuesta HTTP la expone (segundos)."""
    resp = getattr(exc, "response", None)
    hdrs = getattr(resp, "headers", None) if resp is not None else None
    getter = getattr(hdrs, "get", None)
    if callable(getter):
        for clave in ("retry-after", "retry_after"):
            raw = getter(clave)
            if raw is not None:
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    continue

    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err_obj = body.get("error")
        if isinstance(err_obj, dict):
            nested = err_obj.get("retry_after") or err_obj.get("retryAfter")
            if nested is not None:
                try:
                    return float(nested)
                except (TypeError, ValueError):
                    pass

    meta = getattr(exc, "meta", None)
    if hasattr(meta, "retry_after"):  # type: ignore[attr-defined]
        raw = getattr(meta, "retry_after", None)
        if isinstance(raw, (float, int)) and raw >= 0:
            return float(raw)

    return None


def _espera_reintento_rate_limit(exc: RateLimitError, intento: int) -> float:
    ra = _segundos_retry_after(exc)
    if ra is not None and ra > 0:
        return min(max(ra, 0.5), 120.0)
    return min((2 ** intento) * 2.5, 45.0)


def _mensaje_limite_velocidad_desde(exc: RateLimitError) -> str:
    cuerpo = (
        "Tu cuenta alcanzó el **límite de uso** de la API de OpenAI (peticiones por minuto o "
        "tokens por minuto según tu plan). **No es un fallo de esta aplicación.** "
        "En modo streaming puede verse solo el mensaje de error porque la API rechaza "
        "la petición antes de enviar texto."
    )
    seg_h = _segundos_retry_after(exc)
    if seg_h is not None:
        cuerpo += f" Podrías reintentar en unos **{int(seg_h)}** segundos (según el servicio)."
    cuerpo += (
        " Prueba **`gpt-4o-mini`**, espera antes de repetir peticiones "
        "o revisa uso y límites en tu panel de cuenta en OpenAI."
    )
    return cuerpo


class ClaveApiOpenAiAusenteError(RuntimeError):
    """API key ausente o inválida; mensaje destinado a la UI."""

    pass


class OpenAiClienteError(RuntimeError):
    """Error de llamada OpenAI traducido a mensaje para el usuario."""

    pass


T_reintento = TypeVar("T_reintento")


def _llamar_con_reintentos_rate_limit(
    operacion: Callable[[], T_reintento],
) -> T_reintento:
    """Reintenta ``operacion()`` hasta ``_MAX_INTENTOS_RATE_LIMIT`` si hay ``RateLimitError``."""
    ultima_exc: RateLimitError | None = None
    for intento in range(_MAX_INTENTOS_RATE_LIMIT):
        try:
            return operacion()
        except RateLimitError as exc:
            ultima_exc = exc
            if intento >= _MAX_INTENTOS_RATE_LIMIT - 1:
                break
            time.sleep(_espera_reintento_rate_limit(exc, intento))
    assert ultima_exc is not None
    raise OpenAiClienteError(_mensaje_limite_velocidad_desde(ultima_exc)) from ultima_exc


def _mensaje_clave_invalida() -> str:
    return (
        "Configura una clave API válida en la variable **OPENAI_API_KEY** dentro del "
        "archivo **`.env`** (en la raíz del proyecto)."
    )


def _mensaje_conexion() -> str:
    return (
        "No se pudo conectar con la API de OpenAI (tiempo de espera o red). "
        "Comprueba tu conexión e inténtalo de nuevo."
    )


def _mensaje_error_generico(codigo: str | int | None) -> str:
    suf = f" (código {codigo})" if codigo is not None else ""
    return (
        f"La API de OpenAI devolvió un error{suf}. "
        "Revisa el modelo elegido y el estado del servicio."
    )


@dataclass
class ConfiguracionOpenai:
    """Credenciales y transporte para el cliente OpenAI."""

    api_key: str | None = None
    base_url: str | None = None
    timeout_segundos: float = 180.0

    @classmethod
    def desde_variables_entorno(cls) -> ConfiguracionOpenai:
        load_dotenv()
        clave = os.environ.get("OPENAI_API_KEY")
        api_key = (clave.strip() if isinstance(clave, str) else None) or None
        base = os.environ.get("OPENAI_BASE_URL")
        base_url = (base.strip() if base else None) or None
        tiempo = os.environ.get("OPENAI_TIMEOUT")
        timeout_segundos = 180.0
        if tiempo and tiempo.strip():
            try:
                timeout_segundos = float(tiempo.strip())
            except ValueError:
                timeout_segundos = 180.0
        return cls(api_key=api_key, base_url=base_url, timeout_segundos=timeout_segundos)

    def tiene_api_key(self) -> bool:
        return bool(self.api_key and self.api_key.strip())


class ClienteOpenAi:
    """Invoca ``chat.completions`` con los mismos mensajes que usa Ollama (``role`` / ``content``)."""

    def __init__(self, configuracion: ConfiguracionOpenai) -> None:
        self._config = configuracion

    @property
    def configuracion(self) -> ConfiguracionOpenai:
        return self._config

    def chat(self, mensajes: list[dict[str, str]], *, modelo: str) -> str:
        """Generación no streaming; ``modelo`` debe ser un id soportado por la cuenta."""
        if not self._config.tiene_api_key():
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida())

        kwargs: dict = {
            "api_key": self._config.api_key,
            "timeout": self._config.timeout_segundos,
        }
        if self._config.base_url:
            kwargs["base_url"] = self._config.base_url

        cliente = OpenAI(**kwargs)
        try:

            def crear_completacion_no_stream():
                return cliente.chat.completions.create(
                    model=modelo,
                    messages=mensajes,  # type: ignore[arg-type]
                )

            respuesta = _llamar_con_reintentos_rate_limit(crear_completacion_no_stream)
        except AuthenticationError as exc:
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida()) from exc
        except PermissionDeniedError as exc:
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida()) from exc
        except (APIConnectionError, APITimeoutError) as exc:
            raise OpenAiClienteError(_mensaje_conexion()) from exc
        except BadRequestError as exc:
            codigo = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc
        except InternalServerError as exc:
            codigo = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc
        except APIStatusError as exc:
            codigo = getattr(exc, "status_code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc
        except OpenAiClienteError:
            raise
        except Exception as exc:
            codigo = getattr(exc, "status_code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc

        eleccion = respuesta.choices[0].message.content
        if eleccion is None:
            return ""
        return str(eleccion)

    def chat_stream(
        self, mensajes: list[dict[str, str]], *, modelo: str
    ) -> Iterator[str]:
        """Streaming desde ``chat.completions`` con ``stream=True`` (fragmentos de texto)."""
        if not self._config.tiene_api_key():
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida())

        kwargs: dict = {
            "api_key": self._config.api_key,
            "timeout": self._config.timeout_segundos,
        }
        if self._config.base_url:
            kwargs["base_url"] = self._config.base_url

        cliente = OpenAI(**kwargs)

        try:

            def crear_flujo_stream():
                return cliente.chat.completions.create(
                    model=modelo,
                    messages=mensajes,  # type: ignore[arg-type]
                    stream=True,
                )

            flujo = _llamar_con_reintentos_rate_limit(crear_flujo_stream)
        except AuthenticationError as exc:
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida()) from exc
        except PermissionDeniedError as exc:
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida()) from exc
        except (APIConnectionError, APITimeoutError) as exc:
            raise OpenAiClienteError(_mensaje_conexion()) from exc
        except BadRequestError as exc:
            codigo = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc
        except InternalServerError as exc:
            codigo = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc
        except APIStatusError as exc:
            codigo = getattr(exc, "status_code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc
        except OpenAiClienteError:
            raise
        except Exception as exc:
            codigo = getattr(exc, "status_code", None)
            raise OpenAiClienteError(_mensaje_error_generico(codigo)) from exc

        try:
            for fragmento in flujo:
                opciones = getattr(fragmento, "choices", None) or ()
                if not opciones:
                    continue
                delta = getattr(opciones[0], "delta", None)
                if delta is None:
                    continue
                pedazo = getattr(delta, "content", None)
                if pedazo:
                    yield str(pedazo)
        except RateLimitError as exc:
            raise OpenAiClienteError(_mensaje_limite_velocidad_desde(exc)) from exc
        except AuthenticationError as exc:
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida()) from exc
        except PermissionDeniedError as exc:
            raise ClaveApiOpenAiAusenteError(_mensaje_clave_invalida()) from exc
        except (APIConnectionError, APITimeoutError) as exc:
            raise OpenAiClienteError(_mensaje_conexion()) from exc


__all__ = [
    "ClienteOpenAi",
    "ConfiguracionOpenai",
    "ClaveApiOpenAiAusenteError",
    "MODELOS_OPENAI_SOPORTADOS",
    "MODELO_OPENAI_CHATGPT_4O_LATEST",
    "MODELO_OPENAI_GPT_35_TURBO",
    "MODELO_OPENAI_GPT_4_TURBO",
    "MODELO_OPENAI_GPT_4O",
    "MODELO_OPENAI_GPT_4O_MINI",
    "OpenAiClienteError",
]
