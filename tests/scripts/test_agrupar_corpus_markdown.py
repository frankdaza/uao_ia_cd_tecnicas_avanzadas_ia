"""Pruebas de scripts.agrupar_corpus_markdown (fusion determinista y copia de no agrupados)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts import agrupar_corpus_markdown as agr


def _yaml_config(tmp: Path, grupos: list[dict]) -> Path:
    cfg = tmp / "config" / "test_agrupacion.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        yaml.safe_dump({"version": 1, "grupos": grupos}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return cfg


def test_agrupacion_basica_y_copia_resto(tmp_path: Path) -> None:
    ent = tmp_path / "data" / "markdown" / "corp"
    ent.mkdir(parents=True)
    (ent / "buscador-integral-q-aaa.md").write_text(
        "---\ntitulo: A\nsource_url: https://ejemplo.org/a\nseccion: x\n---\n\nTexto A.\n",
        encoding="utf-8",
    )
    (ent / "buscador-integral-q-bbb.md").write_text(
        "---\ntitulo: B\nsource_url: https://ejemplo.org/b\nseccion: x\n---\n\nTexto B.\n",
        encoding="utf-8",
    )
    (ent / "directorio-medico-juan.md").write_text(
        "---\ntitulo: J\nsource_url: https://ejemplo.org/j\nseccion: d\n---\n\nBio Juan.\n",
        encoding="utf-8",
    )
    (ent / "protocolo-z.md").write_text(
        "---\ntitulo: Z\nsource_url: https://ejemplo.org/z\nseccion: p\n---\n\nSolo Z.\n",
        encoding="utf-8",
    )

    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "g_bus",
                "patron_nombre": "buscador-integral-q-*.md",
                "archivo_salida": "agrupado/bus.md",
                "titulo": "Bus consolidado",
                "seccion": "bus",
                "source_url_canonica": "https://ejemplo.org/bus/",
            },
            {
                "id": "g_dir",
                "patron_nombre": "directorio-medico-*.md",
                "archivo_salida": "agrupado/dir.md",
                "titulo": "Dir consolidado",
                "seccion": "dir",
                "source_url_canonica": "",
            },
        ],
    )
    _, grupos = agr.cargar_configuracion_grupos(cfg_path)
    sal = tmp_path / "data" / "processed" / "markdown_agrupado" / "corp"
    stats = agr.ejecutar_agrupacion(
        tmp_path,
        ent,
        sal,
        grupos,
        solo_grupos=False,
        limpiar_salida=False,
    )
    assert stats.grupos_escritos == 2
    assert stats.archivos_copiados == 1
    bus = (sal / "agrupado" / "bus.md").read_text(encoding="utf-8")
    assert "Texto A." in bus and "Texto B." in bus
    assert "https://ejemplo.org/a" in bus and "https://ejemplo.org/b" in bus
    assert bus.index("buscador-integral-q-aaa") < bus.index("buscador-integral-q-bbb")
    assert (sal / "protocolo-z.md").is_file()


def test_solo_grupos_no_copia_huerfanos(tmp_path: Path) -> None:
    ent = tmp_path / "data" / "markdown" / "corp2"
    ent.mkdir(parents=True)
    (ent / "buscador-integral-q-uno.md").write_text(
        "---\ntitulo: U\nsource_url: https://u\nseccion: s\n---\n\nCuerpo.\n",
        encoding="utf-8",
    )
    (ent / "suelto.md").write_text(
        "---\ntitulo: S\nsource_url: https://s\nseccion: s\n---\n\nSuelto.\n",
        encoding="utf-8",
    )
    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "g1",
                "patron_nombre": "buscador-integral-q-*.md",
                "archivo_salida": "agrupado/out.md",
                "titulo": "T",
                "seccion": "s",
            },
        ],
    )
    _, grupos = agr.cargar_configuracion_grupos(cfg_path)
    sal = tmp_path / "data" / "processed" / "markdown_agrupado" / "corp2"
    stats = agr.ejecutar_agrupacion(
        tmp_path,
        ent,
        sal,
        grupos,
        solo_grupos=True,
        limpiar_salida=False,
    )
    assert stats.archivos_copiados == 0
    assert not (sal / "suelto.md").exists()
    assert (sal / "agrupado" / "out.md").is_file()


def test_archivo_salida_duplicado_en_config_falla(tmp_path: Path) -> None:
    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "a",
                "patron_nombre": "a-*.md",
                "archivo_salida": "mismo.md",
                "titulo": "t",
                "seccion": "s",
            },
            {
                "id": "b",
                "patron_nombre": "b-*.md",
                "archivo_salida": "mismo.md",
                "titulo": "t2",
                "seccion": "s2",
            },
        ],
    )
    with pytest.raises(ValueError, match="duplicado"):
        agr.cargar_configuracion_grupos(cfg_path)


def test_limpiar_salida_requiere_segmento_seguro(tmp_path: Path) -> None:
    ent = tmp_path / "in"
    ent.mkdir()
    (ent / "buscador-integral-q-x.md").write_text(
        "---\ntitulo: T\nsource_url: https://x\nseccion: s\n---\n\nX.\n",
        encoding="utf-8",
    )
    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "g",
                "patron_nombre": "buscador-integral-q-*.md",
                "archivo_salida": "out.md",
                "titulo": "T",
                "seccion": "s",
            },
        ],
    )
    _, grupos = agr.cargar_configuracion_grupos(cfg_path)
    sal_inseguro = tmp_path / "salida_peligrosa"
    with pytest.raises(ValueError, match="refuse limpiar"):
        agr.ejecutar_agrupacion(
            tmp_path,
            ent,
            sal_inseguro,
            grupos,
            solo_grupos=True,
            limpiar_salida=True,
        )


def test_patron_nombre_lista_y_servicios_q_antes_de_servicios(tmp_path: Path) -> None:
    """Varios patrones por grupo (indice sin sufijo) y orden servicios-q antes que servicios-*."""
    ent = tmp_path / "data" / "markdown" / "corp_multi"
    ent.mkdir(parents=True)
    (ent / "directorio-medico.md").write_text(
        "---\ntitulo: Indice\nsource_url: https://ejemplo.org/dir\nseccion: d\n---\n\nIndice dir.\n",
        encoding="utf-8",
    )
    (ent / "directorio-medico-juan.md").write_text(
        "---\ntitulo: J\nsource_url: https://ejemplo.org/j\nseccion: d\n---\n\nBio.\n",
        encoding="utf-8",
    )
    (ent / "servicios-q-abc.md").write_text(
        "---\ntitulo: Q\nsource_url: https://ejemplo.org/q\nseccion: s\n---\n\nListado q.\n",
        encoding="utf-8",
    )
    (ent / "servicios-cardio.md").write_text(
        "---\ntitulo: C\nsource_url: https://ejemplo.org/c\nseccion: s\n---\n\nCardio.\n",
        encoding="utf-8",
    )
    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "dir",
                "patron_nombre": ["directorio-medico-*.md", "directorio-medico.md"],
                "archivo_salida": "agrupado/dir.md",
                "titulo": "Dir",
                "seccion": "dir",
            },
            {
                "id": "q",
                "patron_nombre": "servicios-q-*.md",
                "archivo_salida": "agrupado/q.md",
                "titulo": "Q",
                "seccion": "q",
            },
            {
                "id": "srv",
                "patron_nombre": ["servicios-*.md", "servicios.md"],
                "archivo_salida": "agrupado/srv.md",
                "titulo": "Srv",
                "seccion": "srv",
            },
        ],
    )
    _, grupos = agr.cargar_configuracion_grupos(cfg_path)
    sal = tmp_path / "data" / "processed" / "markdown_agrupado" / "corp_multi"
    stats = agr.ejecutar_agrupacion(
        tmp_path,
        ent,
        sal,
        grupos,
        solo_grupos=True,
        limpiar_salida=False,
    )
    assert stats.grupos_escritos == 3
    dir_txt = (sal / "agrupado" / "dir.md").read_text(encoding="utf-8")
    assert "Indice dir." in dir_txt and "Bio." in dir_txt
    assert dir_txt.index("directorio-medico") < dir_txt.index("directorio-medico-juan")
    q_txt = (sal / "agrupado" / "q.md").read_text(encoding="utf-8")
    assert "Listado q." in q_txt
    srv_txt = (sal / "agrupado" / "srv.md").read_text(encoding="utf-8")
    assert "Cardio." in srv_txt
    assert "Listado q." not in srv_txt


def test_patron_nombre_lista_vacia_falla(tmp_path: Path) -> None:
    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "x",
                "patron_nombre": ["  ", ""],
                "archivo_salida": "out.md",
                "titulo": "T",
                "seccion": "s",
            },
        ],
    )
    with pytest.raises(ValueError, match="vacio"):
        agr.cargar_configuracion_grupos(cfg_path)


def test_fuente_yaml_invalida_se_omite_sin_romper_grupo(tmp_path: Path) -> None:
    ent = tmp_path / "data" / "markdown" / "corp3"
    ent.mkdir(parents=True)
    (ent / "buscador-integral-q-bueno.md").write_text(
        "---\ntitulo: B\nsource_url: https://b\nseccion: s\n---\n\nOK.\n",
        encoding="utf-8",
    )
    (ent / "buscador-integral-q-mal.md").write_text(
        "---\n[ invalid\n---\n\nNo.\n",
        encoding="utf-8",
    )
    cfg_path = _yaml_config(
        tmp_path,
        [
            {
                "id": "g",
                "patron_nombre": "buscador-integral-q-*.md",
                "archivo_salida": "agrupado/mezcla.md",
                "titulo": "T",
                "seccion": "s",
            },
        ],
    )
    _, grupos = agr.cargar_configuracion_grupos(cfg_path)
    sal = tmp_path / "data" / "processed" / "markdown_agrupado" / "corp3"
    stats = agr.ejecutar_agrupacion(
        tmp_path,
        ent,
        sal,
        grupos,
        solo_grupos=True,
        limpiar_salida=False,
    )
    assert stats.archivos_grupo_omitidos_yaml >= 1
    texto = (sal / "agrupado" / "mezcla.md").read_text(encoding="utf-8")
    assert "OK." in texto
    assert any("mal" in a.lower() or "yaml" in a.lower() for a in stats.advertencias)


def test_eval_consultas_json_parseable(tmp_path: Path) -> None:
    from scripts import eval_recuperacion_consultas as ev

    p = tmp_path / "c.json"
    p.write_text(
        '{"version":1,"consultas":["uno","dos"]}\n',
        encoding="utf-8",
    )
    c = ev.cargar_consultas(p)
    assert c == ["uno", "dos"]
