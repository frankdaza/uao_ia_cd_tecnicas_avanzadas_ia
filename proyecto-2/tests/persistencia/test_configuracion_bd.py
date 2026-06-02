"""Pruebas de normalizacion de URL de base de datos."""

from src.configuracion import Configuracion


def test_normaliza_postgres_url_compose() -> None:
    cfg = Configuracion(
        _env_file=None,
        database_url="postgres://user:pass@postgres:5432/taam?sslmode=disable",
    )
    async_url = cfg.url_base_datos_async()
    assert async_url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in async_url
    assert "?" not in async_url
    assert async_url.endswith("/taam")
    assert cfg.url_base_datos_sync().startswith("postgresql+psycopg://")


def test_ensambla_url_desde_postgres_star() -> None:
    cfg = Configuracion.model_construct(
        postgres_host="127.0.0.1",
        postgres_port=15433,
        postgres_db="taam",
        postgres_user="postgres",
        postgres_password="secret",
        database_url="",
    )
    url = cfg.url_base_datos_async()
    assert "postgresql+asyncpg://postgres:secret@127.0.0.1:15433/taam" == url


def test_defaults_sembrar_demo() -> None:
    cfg = Configuracion(_env_file=None)
    assert cfg.taam_sembrar_demo_habilitado is False
    assert cfg.taam_sembrar_demo_con_ingesta is True
