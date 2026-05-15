"""Pruebas de scripts.limpiar_corpus_markdown (reglas YAML, exclusion, idempotencia)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts import limpiar_corpus_markdown as limp


def _yaml_limpieza(tmp: Path, extra: dict | None = None) -> Path:
    base = {
        "version": 1,
        "excluir_archivos": ["buscador-integral-q-*.md"],
        "remover_bloques": [
            {
                "nombre": "otros_especialistas_hasta_siguiente_h2",
                "regex_inicio": r"^#{1,6}\s+Otros especialistas\b.*$",
                "hasta_proximo_h2": True,
            },
            {
                "nombre": "navegacion_encuentra",
                "regex_inicio": r"^###\s+Encuentra\b.*$",
                "regex_fin": r"^#\s+",
            },
        ],
        "remover_lineas": [
            {
                "nombre": "redes",
                "regex": r"^\s*\[.*\]\(https://(www\.)?facebook\.com/.*\)\s*$",
            }
        ],
        "minimo_caracteres_utiles": 200,
    }
    if extra:
        base.update(extra)
    cfg = tmp / "limpieza_test.yaml"
    cfg.write_text(
        yaml.safe_dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return cfg


def test_quita_bloque_otros_especialistas(tmp_path: Path) -> None:
    cfg_path = _yaml_limpieza(tmp_path)
    cfg = limp.cargar_configuracion_limpieza(cfg_path)
    ent = tmp_path / "in"
    ent.mkdir()
    body = """# Medico X

Bio unica.

## Otros especialistas de prueba

[Otro](https://ejemplo.org/o)

## Seccion util

Texto final con suficiente longitud para superar el umbral de caracteres utiles en el documento limpio.
""" + ("x" * 120)
    (ent / "ficha.md").write_text(
        "---\ntitulo: X\nsource_url: https://ejemplo.org/x\nseccion: d\n---\n\n" + body,
        encoding="utf-8",
    )
    sal = tmp_path / "out" / "markdown_limpio" / "corp"
    limp.ejecutar_limpieza(tmp_path, ent, sal, cfg, limpiar_salida=False, limit=None)
    out = (sal / "ficha.md").read_text(encoding="utf-8")
    assert "Otros especialistas" not in out
    assert "[Otro](https://ejemplo.org/o)" not in out
    assert "Bio unica." in out
    assert "## Seccion util" in out


def test_excluye_buscador_integral(tmp_path: Path) -> None:
    cfg_path = _yaml_limpieza(tmp_path)
    cfg = limp.cargar_configuracion_limpieza(cfg_path)
    ent = tmp_path / "in"
    ent.mkdir()
    (ent / "buscador-integral-q-abc123.md").write_text(
        "---\ntitulo: B\nsource_url: https://ejemplo.org/b\nseccion: x\n---\n\nContenido.\n",
        encoding="utf-8",
    )
    (ent / "ok.md").write_text(
        "---\ntitulo: O\nsource_url: https://ejemplo.org/o\nseccion: y\n---\n\n"
        + "# T\n\n"
        + ("texto " * 80),
        encoding="utf-8",
    )
    sal = tmp_path / "out" / "markdown_limpio" / "corp"
    limp.ejecutar_limpieza(tmp_path, ent, sal, cfg, limpiar_salida=False, limit=None)
    assert not (sal / "buscador-integral-q-abc123.md").exists()
    assert (sal / "ok.md").is_file()


def test_descarta_por_minimo_caracteres_utiles(tmp_path: Path) -> None:
    cfg_path = _yaml_limpieza(tmp_path, {"minimo_caracteres_utiles": 500})
    cfg = limp.cargar_configuracion_limpieza(cfg_path)
    ent = tmp_path / "in"
    ent.mkdir()
    (ent / "corto.md").write_text(
        "---\ntitulo: C\nsource_url: https://ejemplo.org/c\nseccion: z\n---\n\n# X\n\npequeno.\n",
        encoding="utf-8",
    )
    sal = tmp_path / "out" / "markdown_limpio" / "corp"
    limp.ejecutar_limpieza(tmp_path, ent, sal, cfg, limpiar_salida=False, limit=None)
    assert not (sal / "corto.md").exists()
    man = (sal / "_manifest_limpieza.json").read_text(encoding="utf-8")
    assert "archivos_descartados_por_minimo" in man


def test_idempotencia_segunda_corrida_no_reescribe(tmp_path: Path) -> None:
    cfg_path = _yaml_limpieza(tmp_path)
    cfg = limp.cargar_configuracion_limpieza(cfg_path)
    ent = tmp_path / "in"
    ent.mkdir()
    (ent / "doc.md").write_text(
        "---\ntitulo: D\nsource_url: https://ejemplo.org/d\nseccion: s\n---\n\n"
        + "# T\n\n"
        + ("parrafo largo " * 40),
        encoding="utf-8",
    )
    sal = tmp_path / "out" / "markdown_limpio" / "corp"
    s1 = limp.ejecutar_limpieza(
        tmp_path, ent, sal, cfg, limpiar_salida=False, limit=None
    )
    assert s1.archivos_escritos >= 1
    mtime = (sal / "doc.md").stat().st_mtime_ns
    s2 = limp.ejecutar_limpieza(
        tmp_path, ent, sal, cfg, limpiar_salida=False, limit=None
    )
    assert s2.archivos_omitidos_sin_cambio >= 1
    assert s2.archivos_escritos == 0
    assert (sal / "doc.md").stat().st_mtime_ns == mtime


def test_yaml_regla_bloque_sin_fin_es_error(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "excluir_archivos": [],
                "remover_bloques": [{"nombre": "x", "regex_inicio": "^foo$"}],
                "remover_lineas": [],
                "minimo_caracteres_utiles": 0,
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="regex_fin"):
        limp.cargar_configuracion_limpieza(cfg)


def test_front_matter_literal_preservado(tmp_path: Path) -> None:
    cfg_path = _yaml_limpieza(tmp_path)
    cfg = limp.cargar_configuracion_limpieza(cfg_path)
    ent = tmp_path / "in"
    ent.mkdir()
    fm = "---\ntitulo: 'Tilde: áéí'\nsource_url: https://ejemplo.org/\nseccion: s\n---\n\n"
    (ent / "lit.md").write_text(
        fm + "[Facebook](https://www.facebook.com/x)\n\n# C\n\n" + ("cuerpo " * 50),
        encoding="utf-8",
    )
    sal = tmp_path / "out" / "markdown_limpio" / "corp"
    limp.ejecutar_limpieza(tmp_path, ent, sal, cfg, limpiar_salida=False, limit=None)
    out = (sal / "lit.md").read_text(encoding="utf-8")
    assert "titulo: 'Tilde: áéí'" in out
    assert "facebook.com" not in out


def test_limpiar_salida_requiere_segmento_markdown_limpio(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="markdown_limpio"):
        limp._asegurar_limpiar_salida_segura(Path("/tmp/sin_segmento/out"))
