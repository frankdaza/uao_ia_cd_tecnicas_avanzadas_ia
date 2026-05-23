"""Pruebas del modelo ORM Usuario (sin motor de base de datos)."""

from __future__ import annotations

from sqlalchemy import UniqueConstraint

from src.persistencia.modelos import Base, Usuario


def test_tabla_usuarios_en_metadata() -> None:
    assert "usuarios" in Base.metadata.tables


def test_columnas_usuario() -> None:
    tabla = Usuario.__table__
    nombres = {c.name for c in tabla.columns}
    assert nombres == {
        "id",
        "documento_identidad",
        "nombre",
        "created_at",
        "updated_at",
        "last_login_at",
    }


def test_documento_identidad_unico() -> None:
    col = Usuario.__table__.c.documento_identidad
    assert col.unique is True


def test_restriccion_unica_documento() -> None:
    uniques = [
        c for c in Usuario.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert len(uniques) == 1
    assert list(uniques[0].columns.keys()) == ["documento_identidad"]
