"""Configuracion Ruta B (OpenFang) via variables de entorno (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
