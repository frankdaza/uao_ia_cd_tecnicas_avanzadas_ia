"""Cliente HTTP minimo para la API de chat de Ollama (sin pipeline RAG ni UI)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv

# Tags literales acordados para la interfaz (validacion en capas superiores).
MODELO_LLAMA_3_1_8B = "llama3.1:8b"
MODELO_GEMMA_4_E2B = "gemma4:e2b"
MODELOS_OLLAMA_SOPORTADOS: tuple[str, ...] = (MODELO_LLAMA_3_1_8B, MODELO_GEMMA_4_E2B)


def _mensaje_ollama_inaccesible(base_url: str) -> str:
    return (
        f"No se puede conectar a Ollama en `{base_url}`. "
        "Verifica que `ollama serve` esté corriendo."
    )


def _mensaje_modelo_no_disponible(modelo: str) -> str:
    return (
        f"El modelo `{modelo}` no está instalado en Ollama. "
        f"Ejecuta: `ollama pull {modelo}`"
    )


class OllamaNoAccesibleError(RuntimeError):
    """Se lanza ante timeout o rechazo de conexion hacia ``base_url``.

    Mensaje tipico (sustituye ``{base_url}`` por la URL configurada)::

        No se puede conectar a Ollama en `{base_url}`. Verifica que `ollama serve` esté corriendo.
    """


class ModeloNoDisponibleError(RuntimeError):
    """Se lanza cuando Ollama indica que el modelo no esta instalado.

    Mensaje tipico (sustituye ``{modelo}`` por el nombre del modelo)::

        El modelo `{modelo}` no está instalado en Ollama. Ejecuta: `ollama pull {modelo}`
    """


@dataclass
class ConfiguracionLlm:
    """Parametros de transporte hacia Ollama.

    Para cargar ``OLLAMA_BASE_URL`` y ``MODELO_LLM_DEFECTO`` desde el entorno
    (y opcionalmente un archivo ``.env``), usar :meth:`desde_variables_entorno`.

    ``num_ctx`` fija la ventana del modelo; documentacion del MVP: si un documento
    supera ese limite en tokens, el modelo puede truncar el contexto.
    """

    base_url: str = "http://localhost:11434"
    modelo: str = MODELO_LLAMA_3_1_8B
    temperatura: float = 0.2
    num_ctx: int = 8192
    timeout_segundos: int = 180

    @classmethod
    def desde_variables_entorno(cls) -> ConfiguracionLlm:
        """Lee variables de entorno tras ``load_dotenv()`` (si existe ``.env``)."""
        load_dotenv()
        base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        modelo = os.environ.get("MODELO_LLM_DEFECTO", MODELO_LLAMA_3_1_8B).strip()
        return cls(
            base_url=base.rstrip("/"),
            modelo=modelo,
        )


class ClienteOllama:
    """Envia mensajes a ``POST /api/chat`` y lista modelos con ``GET /api/tags``."""

    def __init__(self, configuracion: ConfiguracionLlm) -> None:
        self._config = configuracion
        self._sesion = requests.Session()

    @property
    def configuracion(self) -> ConfiguracionLlm:
        """Misma instancia de :class:`ConfiguracionLlm` usada en ``chat`` y peticiones."""
        return self._config

    def _url(self, ruta: str) -> str:
        return f"{self._config.base_url.rstrip('/')}{ruta}"

    def _peticion(
        self,
        metodo: str,
        ruta: str,
        *,
        json_cuerpo: dict[str, Any] | None = None,
    ) -> requests.Response:
        ultima: requests.Response | None = None
        for intento in range(2):
            try:
                resp = self._sesion.request(
                    metodo,
                    self._url(ruta),
                    json=json_cuerpo,
                    timeout=self._config.timeout_segundos,
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                raise OllamaNoAccesibleError(
                    _mensaje_ollama_inaccesible(self._config.base_url)
                ) from exc

            if resp.status_code >= 500 and intento == 0:
                time.sleep(2)
                ultima = resp
                continue
            return resp

        assert ultima is not None
        ultima.raise_for_status()
        return ultima

    def _error_modelo_en_cuerpo(self, datos: dict[str, Any]) -> bool:
        err = str(datos.get("error", "")).lower()
        return "not found" in err and "model" in err

    def _interpretar_fallo_modelo(self, resp: requests.Response) -> None:
        modelo = self._config.modelo
        try:
            datos = resp.json()
        except requests.JSONDecodeError:
            datos = {}
        if self._error_modelo_en_cuerpo(datos):
            raise ModeloNoDisponibleError(_mensaje_modelo_no_disponible(modelo))
        if resp.status_code == 404:
            raise ModeloNoDisponibleError(_mensaje_modelo_no_disponible(modelo))

    def chat(self, mensajes: list[dict[str, str]]) -> str:
        """Envia ``messages`` a Ollama y devuelve el texto de ``message.content``."""
        cuerpo: dict[str, Any] = {
            "model": self._config.modelo,
            "messages": mensajes,
            "stream": False,
            "options": {
                "temperature": self._config.temperatura,
                "num_ctx": self._config.num_ctx,
            },
        }
        resp = self._peticion("POST", "/api/chat", json_cuerpo=cuerpo)

        if resp.status_code >= 400:
            self._interpretar_fallo_modelo(resp)
            resp.raise_for_status()

        datos = resp.json()
        if self._error_modelo_en_cuerpo(datos):
            raise ModeloNoDisponibleError(
                _mensaje_modelo_no_disponible(self._config.modelo)
            )

        mensaje = datos.get("message") or {}
        contenido = mensaje.get("content")
        if contenido is None:
            return ""
        return str(contenido)

    def listar_modelos_locales(self) -> list[str]:
        """Devuelve los tags instalados segun ``GET /api/tags``."""
        resp = self._peticion("GET", "/api/tags")
        resp.raise_for_status()
        datos = resp.json()
        modelos = datos.get("models") or []
        nombres: list[str] = []
        for item in modelos:
            nombre = item.get("name") if isinstance(item, dict) else None
            if nombre:
                nombres.append(str(nombre))
        return nombres
