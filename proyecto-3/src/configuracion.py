"""Configuracion Ruta B (OpenFang) via variables de entorno (pydantic-settings)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_AGENTE_DEFAULT = "bot_lili_taam"

_MARCA_WORKSPACE = Path("data") / "markdown"
_RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"


class Configuracion(BaseSettings):
    """Variables de entorno para scripts Python auxiliares de proyecto-3."""

    model_config = SettingsConfigDict(
        env_file=_RUTA_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="OPENAI_EMBEDDING_MODEL",
    )
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    openfang_home: Path = Field(
        default=Path("openfang/data"),
        validation_alias="OPENFANG_HOME",
    )
    openfang_agent_id: str = Field(default="", validation_alias="OPENFANG_AGENT_ID")
    openfang_api_url: str = Field(
        default="http://127.0.0.1:4200",
        validation_alias="OPENFANG_API_URL",
    )
    uao_workspace_root: str = Field(default="", validation_alias="UAO_WORKSPACE_ROOT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias="OLLAMA_BASE_URL",
    )

    def raiz_proyecto(self) -> Path:
        """Directorio ``proyecto-3/`` (donde vive ``pyproject.toml``)."""
        return Path(__file__).resolve().parents[1]

    def raiz_workspace(self) -> Path:
        """
        Raiz del monorepo donde reside ``data/``.

        Orden: ``UAO_WORKSPACE_ROOT``; padre de proyecto-3 si tiene ``data/markdown/``;
        si no, la raiz del proyecto.
        """
        override = self.uao_workspace_root.strip()
        if override:
            return Path(override).resolve()
        proyecto = self.raiz_proyecto()
        padre = proyecto.parent
        if (padre / _MARCA_WORKSPACE).is_dir():
            return padre.resolve()
        if (proyecto / _MARCA_WORKSPACE).is_dir():
            return proyecto.resolve()
        return proyecto.resolve()

    def openfang_home_absoluto(self) -> Path:
        """Ruta absoluta de datos runtime OpenFang (SQLite, JSONL)."""
        home = self.openfang_home
        if home.is_absolute():
            return home.resolve()
        return (self.raiz_proyecto() / home).resolve()

    def ruta_db_openfang(self) -> Path:
        """SQLite del kernel OpenFang 0.6.9 bajo ``{OPENFANG_HOME}/data/openfang.db``."""
        return self.openfang_home_absoluto() / "data" / "openfang.db"

    def resolver_agent_id_openfang(self) -> str:
        """
        UUID del agente destino de la ingesta.

        Orden: ``OPENFANG_AGENT_ID``; si no, ``GET /api/status`` buscando ``bot_lili_taam``.
        """
        override = self.openfang_agent_id.strip()
        if override:
            return override
        url = f"{self.openfang_api_url.rstrip('/')}/api/status"
        try:
            with urllib.request.urlopen(url, timeout=5) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            raise ValueError(
                f"No se pudo resolver el agent_id OpenFang ({_AGENTE_DEFAULT}). "
                f"Define OPENFANG_AGENT_ID o arranca el daemon. Detalle: {exc}"
            ) from exc
        for agente in datos.get("agents", []):
            if agente.get("name") == _AGENTE_DEFAULT:
                agent_id = agente.get("id")
                if isinstance(agent_id, str) and agent_id:
                    return agent_id
        raise ValueError(
            f"Agente '{_AGENTE_DEFAULT}' no encontrado en GET /api/status. "
            "Ejecuta: openfang agent spawn openfang/agents/bot_lili_taam/agent.toml"
        )

    def exigir_openai_api_key(self) -> str:
        """Devuelve la clave OpenAI o lanza si falta (scripts que llaman a la API)."""
        clave = self.openai_api_key.strip()
        if not clave:
            raise ValueError(
                "OPENAI_API_KEY no esta configurada. "
                "Copia proyecto-3/.env.example a .env y define la clave."
            )
        return clave

    def exigir_telegram_bot_token(self) -> str:
        """Devuelve el token del bot Telegram o lanza si falta."""
        token = self.telegram_bot_token.strip()
        if not token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN no esta configurado. "
                "Usa un bot distinto al de proyecto-2 (BotFather)."
            )
        return token


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
