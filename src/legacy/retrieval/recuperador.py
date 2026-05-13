# MVP fase 1: BM25 a nivel archivo. Sin vectores densos ni subdivision interna antes
# de aplicar BM25; el indice es el archivo .md completo.
# Prohibido importar: scikit (modulo *learn* de ML), biblioteca de similitud
# F-A-I-S-S, almacen vectorial Chroma, cliente Qdrant, modelos de oraciones
# preentrenados para embeddings, ni submodulos de *embeddings* de cadenas (LC/LI).

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np
import yaml
from nltk.stem import SnowballStemmer
from rank_bm25 import BM25Okapi

from src.legacy.retrieval._stopwords_nltk_es import STOPWORDS_NLTK_ES
from src.legacy.retrieval.sinonimos import expandir_query

_STOPWORDS_ES_BASE_MANUALES: frozenset[str] = frozenset(
    {
        "de",
        "la",
        "el",
        "en",
        "y",
        "que",
        "los",
        "las",
        "del",
        "un",
        "una",
        "por",
        "con",
        "para",
        "se",
        "su",
        "es",
        "al",
        "lo",
        "a",
        "o",
    }
)

STOPWORDS_ES_UNION: frozenset[str] = frozenset(STOPWORDS_NLTK_ES) | _STOPWORDS_ES_BASE_MANUALES

_TERMINOS_RELACIONADOS_CON_INTERROGATIVOS: frozenset[str] = frozenset(
    {
        "cual",
        "cuales",
        "como",
        "cuando",
        "donde",
        "quien",
        "quienes",
    }
)
# No se aplican antes del stem (evita preguntas vacias tipo Quienes son).

STOPWORDS_EFECTIVAS_PRE_RAIZ_AL_STEMMING: frozenset[str] = (
    STOPWORDS_ES_UNION - _TERMINOS_RELACIONADOS_CON_INTERROGATIVOS
)

UMBRAL_RELATIVO_BM25: float = 0.3
"""Coeficiente minimo contra el mejor score cuando se filtran documentos antes del top-k."""

_STEM_SNOWB_ES: SnowballStemmer | None = None


def obtener_stemmador_espanol() -> SnowballStemmer:
    global _STEM_SNOWB_ES
    if _STEM_SNOWB_ES is None:
        _STEM_SNOWB_ES = SnowballStemmer("spanish")
    return _STEM_SNOWB_ES


def _fabricar_raiz_descart_si_queda_sin_lexico_fuerte(
    muestrario_stop: frozenset[str],
    terminos_permitidos_interrogativo: frozenset[str],
) -> frozenset[str]:
    """
    Descarta raices que provienen de stopwords NLP; interrogativos se conservan
    para preguntas breves (por ejemplo Quienes son).
    """
    stem_motor = obtener_stemmador_espanol()
    raices_desde_stop = frozenset(
        stem_motor.stem(terminacion) for terminacion in muestrario_stop if terminacion
    )
    raices_permitidas = frozenset(
        stem_motor.stem(seg)
        for seg in terminos_permitidos_interrogativo
        if seg
    )
    return frozenset(
        entrada for entrada in raices_desde_stop if entrada not in raices_permitidas
    )


_RAIZ_DESCARTE_POS_STEM: frozenset[str] = (
    _fabricar_raiz_descart_si_queda_sin_lexico_fuerte(
        STOPWORDS_ES_UNION,
        _TERMINOS_RELACIONADOS_CON_INTERROGATIVOS,
    )
)


@dataclass(frozen=True)
class DocumentoRecuperado:
    ruta: Path
    titulo: str
    source_url: str
    contenido: str
    score: float


class RecuperacionVaciaError(Exception):
    """Ningun documento supera el umbral BM25 relativo o la consulta no genera terminos."""


@runtime_checkable
class RecuperadorDocumento(Protocol):
    def buscar(self, pregunta: str) -> DocumentoRecuperado: ...

    def buscar_top(self, pregunta: str, k: int = 3) -> list[DocumentoRecuperado]: ...

    def recargar(self) -> None: ...


def _quitar_marcas_combinantes(texto: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", texto)
        if unicodedata.category(c) != "Mn"
    )


def tokenizar(texto: str) -> list[str]:
    """
    Minusculas, sin tildes, palabras (regex ``\\\\w+``), longitud >= 2 despues del stem,

    sinonimos NLTK español endurecidos, stem Snowball español igual en consulta y documentos indizados.
    """
    t = _quitar_marcas_combinantes(texto)
    t = t.lower()
    stem = obtener_stemmador_espanol()
    out: list[str] = []
    for w in re.findall(r"\w+", t, flags=re.UNICODE):
        if len(w) < 2:
            continue
        if w in STOPWORDS_EFECTIVAS_PRE_RAIZ_AL_STEMMING:
            continue
        raiz = stem.stem(w)
        if len(raiz) < 2:
            continue
        if raiz in _RAIZ_DESCARTE_POS_STEM:
            continue
        out.append(raiz)
    return out


def parsear_markdown(texto: str) -> tuple[dict[str, Any], str]:
    """
    Separa front matter YAML del cuerpo (texto tras el segundo ``---`` en linea).
    Si no hay front matter valido, devuelve ``({}, texto completo)``.
    """
    texto_entrada_sin_ruta_original = texto.lstrip("\ufeff")
    m = re.match(
        r"^---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n?(.*)\Z",
        texto_entrada_sin_ruta_original,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not m:
        return {}, texto_entrada_sin_ruta_original
    yml, cuerpo = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(yml) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, cuerpo


_rx_boiler_cabezal_principal = re.compile(
    # Valledellili: enlaces redes y bloque navegacion comun hasta antes de contenido especifico
    r"^\[\s*Facebook\s*\]\([^\)]+\)\s*$.*?"
    r"^\#{3}\s*Servicios para ti\s*\n",
    flags=re.MULTILINE | re.DOTALL,
)


def limpiar_boilerplate(cuerpo: str) -> str:
    """Quita navegacion global repetida (solo indexacion BM25): si no coincide, devuelve igual."""
    reemplazo = _rx_boiler_cabezal_principal.sub("", cuerpo)
    limpio_local = reemplazo.strip()
    return limpio_local if limpio_local else cuerpo


def texto_indexable_bm25(
    front: dict[str, Any],
    cuerpo_indice_sin_boilerplate: str,
    *,
    peso_titulo: int = 5,
    peso_seccion: int = 3,
) -> str:
    """BM25 simple por campos: repite fragmentos lexicalmente para aumentar ponderacion textual."""
    titulo = str(front.get("titulo", "") or "")
    sec = str(front.get("seccion", "") or "").replace("-", " ")
    partes_segmentos: list[str] = []
    if titulo:
        partes_segmentos.extend([titulo] * peso_titulo)
    if sec:
        partes_segmentos.extend([sec] * peso_seccion)
    partes_segmentos.append(cuerpo_indice_sin_boilerplate)
    return "\n".join(partes_segmentos)


def _omitir_patron_integral_busqueda(nombre_archivo: str, seccion_fm: Any) -> bool:
    lc = nombre_archivo.lower()
    sec_texto = str(seccion_fm or "").lower().strip("/")
    if "buscador-integral-q-" in lc:
        return True
    if sec_texto.startswith("buscador-integral-q"):
        return True
    return False


_re_stem_sufijo_numeracion = re.compile(r"^(.+)-(\d+)$")


def _clave_grupo_coincide_stem_medidas(stem_actual: str) -> str:
    """Agrupa `slug-2` con `slug` para dedupe logico cuando existen sufijos repetidos."""

    coincide = _re_stem_sufijo_numeracion.fullmatch(stem_actual)
    if coincide:
        return coincide.group(1)
    return stem_actual


def _fecha_iso_extracc_texto(fr: dict[str, Any]) -> str | None:
    """Devuelve string ISO yyyy-mm-dd o None cuando falta o es invalido."""
    v = fr.get("fecha_extraccion")
    if isinstance(v, str):
        texto = v.strip().strip("'\"")
        if len(texto) >= 10 and texto[4] == "-" and texto[7] == "-":
            return texto[:10]
        return texto or None
    return None


def _mejor_conjunto_filas_sin_dup(
    registros_filas: list[tuple[Path, dict[str, Any], str]],
) -> tuple[Path, dict[str, Any], str]:
    """Elige mejor documento ante duplicados numerados (--2, --3...) y homonimos slug."""

    def llave_filas_filas(ele: tuple[Path, dict[str, Any], str]) -> tuple:
        rut, frm, cue = ele
        mm = _re_stem_sufijo_numeracion.fullmatch(rut.stem)
        penaliza_solo_sufijo = 1 if mm else 0
        fecha_ord = _fecha_iso_extracc_texto(frm) or "0001-01-01"
        return (fecha_ord, len(cue), -penaliza_solo_sufijo, rut.as_posix().lower())

    return max(registros_filas, key=llave_filas_filas)


def _dedupe_por_basenum_segun_stem_sin_sufijo(
    filas_precargadas: list[tuple[Path, dict[str, Any], str]],
) -> list[tuple[Path, dict[str, Any], str]]:
    """Une archivos tipo `articulo.md` mas `articulo-2.md` si comparten mismo prefijo textual."""

    ordenados_filas_agrupaciones: dict[str, list[tuple[Path, dict[str, Any], str]]]
    ordenados_filas_agrupaciones = {}
    for fila_actual in filas_precargadas:
        claves_stem_actual = fila_actual[0].stem
        etiqueta_grupo_actual = _clave_grupo_coincide_stem_medidas(claves_stem_actual)
        ordenados_filas_agrupaciones.setdefault(etiqueta_grupo_actual, []).append(
            fila_actual
        )
    saliente: list[tuple[Path, dict[str, Any], str]] = []
    for filas_internas_filas_actual in ordenados_filas_agrupaciones.values():
        if len(filas_internas_filas_actual) == 1:
            saliente.extend(filas_internas_filas_actual)
            continue
        saliente.append(
            _mejor_conjunto_filas_sin_dup(list(filas_internas_filas_actual))
        )
    saliente.sort(key=lambda x: x[0].as_posix().lower())
    return saliente


def cargar_corpus(
    directorio_markdown: Path,
    glob_patron_archivos_md: str = "**/*.md",
    *,
    peso_titulo_bm25campo: int = 5,
    peso_seccion_bm25campo: int = 3,
) -> list[tuple[Path, dict[str, Any], str, list[str]]]:
    """Lee Markdown, aplicando higiene opcional antes de BM25 pesado campo-a-campo."""

    base = directorio_markdown.resolve()
    salidas: list[tuple[Path, dict[str, Any], str, list[str]]] = []
    filas_fina_bruta: list[tuple[Path, dict[str, Any], str]] = []
    for ruta_actual in sorted(base.glob(glob_patron_archivos_md), key=lambda pp: pp.as_posix().lower()):
        if not ruta_actual.is_file():
            continue
        raw_actual = ruta_actual.read_text(encoding="utf-8", errors="replace")
        front_actual, cue_actual = parsear_markdown(raw_actual)
        if _omitir_patron_integral_busqueda(ruta_actual.name, front_actual.get("seccion")):
            continue
        filas_fina_bruta.append((ruta_actual, front_actual, cue_actual))
    filas_dedupe = _dedupe_por_basenum_segun_stem_sin_sufijo(filas_fina_bruta)
    for ruta_fd, frm_fd, cuerpo_sin_cambiar in filas_dedupe:
        cuerpo_bm25_limpia = limpiar_boilerplate(cuerpo_sin_cambiar)
        idx_bm25_actual = texto_indexable_bm25(
            frm_fd,
            cuerpo_bm25_limpia,
            peso_titulo=peso_titulo_bm25campo,
            peso_seccion=peso_seccion_bm25campo,
        )
        tokens_actual = tokenizar(idx_bm25_actual)
        salidas.append((ruta_fd, frm_fd, cuerpo_sin_cambiar, tokens_actual))
    return salidas


class RecuperadorBm25:
    def __init__(
        self,
        directorio_markdown: Path,
        glob_patron_archivos_md: str = "**/*.md",
        *,
        peso_titulo_bm25campo: int = 5,
        peso_seccion_bm25campo: int = 3,
        umbral_relativo: float = UMBRAL_RELATIVO_BM25,
    ) -> None:
        self._directorio = directorio_markdown
        self._glob_patron = glob_patron_archivos_md
        self._peso_bm25titulo_campos_repetibles = peso_titulo_bm25campo
        self._peso_seccion = peso_seccion_bm25campo
        self._umbral_relativo = umbral_relativo
        self._rutas: list[Path] = []
        self._titulos: list[str] = []
        self._urls: list[str] = []
        self._cuerpos_crudos: list[str] = []
        self._token_docs_bm25lista: list[list[str]] = []
        self._bm25_obj: BM25Okapi | None = None
        self._reindexar_interno_bm25_okapi()

    def _reindexar_interno_bm25_okapi(self) -> None:
        cargamento = cargar_corpus(
            self._directorio,
            self._glob_patron,
            peso_titulo_bm25campo=self._peso_bm25titulo_campos_repetibles,
            peso_seccion_bm25campo=self._peso_seccion,
        )
        if not cargamento:
            msg = (
                f"No quedaron Markdown sin filtrado en "
                f"{self._directorio!r} (glob original {self._glob_patron!r})."
            )
            raise ValueError(msg)
        self._rutas.clear()
        self._titulos.clear()
        self._urls.clear()
        self._cuerpos_crudos.clear()
        self._token_docs_bm25lista.clear()
        for ruta_i, frm_i, cuerpo_actual, tok_i in cargamento:
            self._rutas.append(ruta_i)
            self._titulos.append(str(frm_i.get("titulo", "") or ""))
            self._urls.append(str(frm_i.get("source_url", "") or ""))
            self._cuerpos_crudos.append(cuerpo_actual)
            self._token_docs_bm25lista.append(tok_i)
        self._bm25_obj = BM25Okapi(self._token_docs_bm25lista)

    def buscar_top(self, pregunta: str, k: int = 3) -> list[DocumentoRecuperado]:
        if self._bm25_obj is None or not self._rutas:
            raise RecuperacionVaciaError("BM25 incompleto: indice falta.")
        pregunta_larga = expandir_query(pregunta)
        lista_palabras = tokenizar(pregunta_larga)
        if not lista_palabras:
            raise RecuperacionVaciaError("La pregunta no produjo terminos despues stem/stop.")

        vectores_bm25_actual = np.asarray(
            self._bm25_obj.get_scores(lista_palabras),
            dtype=np.float64,
        )

        mejor_puntaje_actual = np.max(vectores_bm25_actual)
        condicion_umbral_actual = mejor_puntaje_actual * float(self._umbral_relativo)

        filtros_filas_bm25_actual = vectores_bm25_actual > 0

        filtros_umbral_bm25_actual = filtros_filas_bm25_actual & (
            vectores_bm25_actual >= condicion_umbral_actual
        )
        filtros_bm25_actual = filtros_umbral_bm25_actual
        ubicaciones_pos_actual = np.flatnonzero(filtros_bm25_actual)
        if ubicaciones_pos_actual.size == 0:
            raise RecuperacionVaciaError(
                "Todos los puntajes BM25 bajaron bajo umbral respecto al mejor."
            )

        orden_desc_indices = ubicaciones_pos_actual[
            np.argsort(-vectores_bm25_actual[ubicaciones_pos_actual])
        ]

        numero_max_actual = min(int(k), int(orden_desc_indices.size))
        saliendo_lista_actual: list[DocumentoRecuperado] = []
        for ubicacion_idx in range(numero_max_actual):
            indice_doc_bm25_actual = int(orden_desc_indices[ubicacion_idx])
            saliendo_lista_actual.append(
                DocumentoRecuperado(
                    ruta=self._rutas[indice_doc_bm25_actual],
                    titulo=self._titulos[indice_doc_bm25_actual],
                    source_url=self._urls[indice_doc_bm25_actual],
                    contenido=self._cuerpos_crudos[indice_doc_bm25_actual],
                    score=float(vectores_bm25_actual[indice_doc_bm25_actual]),
                )
            )

        return saliendo_lista_actual

    def buscar(self, pregunta: str) -> DocumentoRecuperado:
        return self.buscar_top(pregunta, k=1)[0]

    def recargar(self) -> None:
        self._reindexar_interno_bm25_okapi()


__all__ = [
    "DocumentoRecuperado",
    "RecuperacionVaciaError",
    "RecuperadorBm25",
    "STOPWORDS_ES_UNION",
    "UMBRAL_RELATIVO_BM25",
    "cargar_corpus",
    "expandir_query",
    "limpiar_boilerplate",
    "parsear_markdown",
    "texto_indexable_bm25",
    "tokenizar",
]
