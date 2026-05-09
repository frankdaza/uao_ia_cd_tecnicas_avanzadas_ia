"""Pruebas del recuperador BM25 a nivel archivo, fixtures e import-guard."""

from __future__ import annotations

import importlib
import inspect
import shutil
import sys
from pathlib import Path

import pytest

from src.retrieval.recuperador import (
    RecuperacionVaciaError,
    RecuperadorBm25,
    cargar_corpus,
    parsear_markdown,
    tokenizar,
)


def test_tokenizacion_tilde_y_minuscula() -> None:
    assert tokenizar("Cardiología") == ["cardiologi"]


def test_tokenizacion_signos() -> None:
    assert tokenizar("¿Dónde queda?") == ["dond", "qued"]


def test_tokenizacion_filtra_stopwords_por_stopword_y_raiz() -> None:
    toks = tokenizar("la fundación es")
    assert "la" not in toks
    assert "es" not in toks
    assert "fundacion" in toks


def test_expandir_query_sinonimo_cita_agrega_terminos() -> None:
    from src.retrieval.sinonimos import expandir_query

    extendida = expandir_query("Necesito cita medica")
    assert "agendar" in extendida and "consulta" in extendida


PREGUNTA_A_ARCHIVO_ESPERADO: list[tuple[str, str]] = [
    ("¿Cuáles son los servicios de cardiología?", "servicios-cardiologia.md"),
    ("Atienden a ninos", "servicios-pediatria.md"),
    ("Cual es la historia de la fundacion", "quienes-somos.md"),
    ("Como los puedo contactar", "contacto.md"),
    ("Quienes son", "quienes-somos.md"),
]


def test_buscar_devuelve_archivo_esperado_al_menos_cuatro_de_cinco(
    dir_fixtures_markdown: Path,
) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    aciertos = 0
    for pregunta, nombre_archivo in PREGUNTA_A_ARCHIVO_ESPERADO:
        doc = recu.buscar(pregunta)
        if doc.ruta.name == nombre_archivo:
            aciertos += 1
    assert aciertos >= 4, f"se esperaban al menos 4/5, hubo {aciertos}/5"


def test_recuperacion_vacia_lanza_excepcion(dir_fixtures_markdown: Path) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    with pytest.raises(RecuperacionVaciaError):
        recu.buscar("blockchain quantum NFT")


def test_buscar_top_ordena_descendente_y_respeta_k(dir_fixtures_markdown: Path) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    pregunta = (
        "fundacion servicios cardiologia pediatria contacto historia lineas region"
    )
    docs3 = recu.buscar_top(pregunta, k=3)
    assert 1 <= len(docs3) <= 3
    scores = [d.score for d in docs3]
    assert scores == sorted(scores, reverse=True)
    assert all(d.score > 0.0 for d in docs3)
    docs2 = recu.buscar_top(pregunta, k=2)
    assert len(docs2) <= 2
    assert docs2[0].ruta == docs3[0].ruta


def test_buscar_top_un_solo_documento_positivo(dir_fixtures_markdown: Path) -> None:
    """Consulta muy especifica: solo un archivo deberia sobresalir claramente."""
    recu = RecuperadorBm25(dir_fixtures_markdown)
    docs = recu.buscar_top("hemodinamia cateter valvulopatia sincronizacion", k=3)
    assert len(docs) >= 1
    assert docs[0].ruta.name == "servicios-cardiologia.md"
    assert len(docs) == 1


def test_buscar_equivale_a_primer_buscar_top(dir_fixtures_markdown: Path) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    pregunta = "Cual es la historia de la fundacion"
    uno = recu.buscar(pregunta)
    lista = recu.buscar_top(pregunta, k=1)
    assert len(lista) == 1
    assert uno.ruta == lista[0].ruta
    assert uno.score == lista[0].score


def test_recargar_reindexa_nuevo_archivo(
    tmp_path: Path,
    dir_fixtures_markdown: Path,
) -> None:
    base = tmp_path / "corpus"
    shutil.copytree(dir_fixtures_markdown, base, dirs_exist_ok=False)
    recu = RecuperadorBm25(base)
    ruta_oda = base / "nuevo-modulo-oda.md"
    ruta_oda.write_text(
        "---\n"
        "titulo: Nuevo servicio de odontologia avanzada\n"
        "source_url: https://fundacion-ejemplo.org/oda\n"
        "---\n"
        "\n# Odontologia avanzada\n"
        "Este es el unico documento que habla de **ortodoncia invisible** y "
        "ortodoncia con alineadores en la fundacion. Cita oda prioritaria.\n",
        encoding="utf-8",
    )
    recu.recargar()
    doc = recu.buscar("ortodoncia invisible alineadores oda")
    assert doc.ruta.name == "nuevo-modulo-oda.md"
    assert "ortodoncia" in doc.contenido.lower()


def _cargar_modulo_recuperador_fresco():
    """
    Carga o recarga el modulo de recuperacion y devuelve el objeto modulo.
    """
    if "src.retrieval.recuperador" in sys.modules:
        return importlib.reload(sys.modules["src.retrieval.recuperador"])
    return importlib.import_module("src.retrieval.recuperador")


def test_recuperador_no_importa_embedding_stack() -> None:
    """No debe cargarse (ni nombrarse en codigo) el stack de vectores listado."""
    prohibidos: tuple[str, ...] = (
        "sklearn",
        "faiss",
        "chromadb",
        "qdrant_client",
        "sentence_transformers",
        "langchain.embeddings",
        "llama_index.embeddings",
    )
    antes = {n for n in prohibidos if n in sys.modules}
    mod = _cargar_modulo_recuperador_fresco()
    fuente = inspect.getsource(mod)
    for nombre in prohibidos:
        assert nombre not in fuente, f"{nombre} no debe aparecer en el codigo"
        assert nombre not in sys.modules or nombre in antes, (
            f"{nombre} quedo en sys.modules sin haber estado antes de importar recuperador"
        )


def test_no_existe_chunking_ni_apis_de_fragmento() -> None:
    mod = _cargar_modulo_recuperador_fresco()
    fuente = inspect.getsource(mod)
    for frag in ("chunk", "split_text", "sliding"):
        assert (
            frag not in fuente
        ), f"subcadena no permitida en el fuente: {frag!r}"
    fragmento_en_nombre = ("chunk", "split_text", "sliding", "tokenize_chunks")
    for nombre in dir(mod):
        if nombre.startswith("_"):
            continue
        for frag in fragmento_en_nombre:
            assert (
                frag not in nombre
            ), f"nombre {nombre!r} contiene {frag!r}"


def test_parsear_markdown_sin_front_matter() -> None:
    texto = "# Solo titulo\n\nCuerpo sin separador."
    meta, cuerpo = parsear_markdown(texto)
    assert meta == {}
    assert "Cuerpo" in cuerpo


def test_cargar_corpus_ordenado(dir_fixtures_markdown: Path) -> None:
    filas = cargar_corpus(dir_fixtures_markdown)
    nombres = [p.name for p, *_ in filas]
    assert nombres == sorted(nombres, key=str.lower)
    assert len(filas) == 5


def test_cargar_corpus_omite_buscador_integral_serp(tmp_path: Path) -> None:
    ruta_ok = tmp_path / "ok.md"
    ruta_ok.write_text(
        "---\ntitulo: Página ok\n---\n\nContenido unico zebra.\n",
        encoding="utf-8",
    )
    ruta_serp = tmp_path / "buscador-integral-q-abc123.md"
    ruta_serp.write_text(
        "---\ntitulo: Ruido SERP\nseccion: buscador-integral-q-xyz\n---\nsnippet\n",
        encoding="utf-8",
    )
    cargado = cargar_corpus(tmp_path)
    assert len(cargado) == 1
    assert cargado[0][0].name == "ok.md"


def test_cargar_corpus_dedupe_elige_actual_y_mas_largo(tmp_path: Path) -> None:
    base = "---\ntitulo: Mismo contenido viejo\nfecha_extraccion: '2026-04-01'\nhash: a\n---\n\nalfa\n"
    nuevo = "---\ntitulo: Actualizado\nfecha_extraccion: '2026-05-01'\nhash: b\n---\n\nbeta extendido linea\n"
    (tmp_path / "documento.md").write_text(base, encoding="utf-8")
    (tmp_path / "documento-2.md").write_text(nuevo, encoding="utf-8")
    cargado = cargar_corpus(tmp_path)
    assert len(cargado) == 1
    assert "beta" in cargado[0][2]


def test_limpiar_boilerplate_quita_bloque_facebook_servicios_para_ti() -> None:
    from src.retrieval.recuperador import limpiar_boilerplate

    mezcla = (
        "---\ntitulo: X\n---\n\n"
        "[Facebook](https://x)\n[y](https://y)\n\n"
        "### Servicios para ti\n\n"
        "## Contenido real\nsolo esto cuenta."
    )
    limpio_local = limpiar_boilerplate(mezcla)
    assert "[Facebook]" not in limpio_local
    assert "solo esto cuenta" in limpio_local
