"""
Ejecuta el dataset de evaluación contra :class:`~src.qa.pipeline.PipelineQa` por modelo
Ollama y escribe un informe Markdown en ``data/processed/evaluaciones/``.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from src.qa.cliente_ollama import ModeloNoDisponibleError
from src.legacy.qa.pipeline import PipelineQa, RespuestaQa, construir_pipeline_por_defecto

# Raíz del repositorio (directorio que contiene ``scripts/`` y ``src/``)
_RAIZ_REPO = Path(__file__).resolve().parent.parent
_DATASET_POR_DEFECTO = _RAIZ_REPO / "tests" / "qa" / "preguntas_evaluacion.yml"
_SALIDA_POR_DEFECTO = _RAIZ_REPO / "data" / "processed" / "evaluaciones"

_FRASE_SIN_INFORMACION = "No tengo información suficiente"


@dataclass
class RegistroEvaluacion:
    """Una fila de resultado por pregunta ejecutada."""

    pregunta_id: int
    texto_pregunta: str
    categoria: str
    archivo_esperado: str | None
    respuesta: RespuestaQa
    indice_muestra: int

    @property
    def acierto_archivo(self) -> bool | None:
        if not self.archivo_esperado:
            return None
        if not self.respuesta.archivo_fuente:
            return False
        return self.respuesta.archivo_fuente.name == self.archivo_esperado

    @property
    def es_respuesta_sin_informacion(self) -> bool:
        return _FRASE_SIN_INFORMACION in (self.respuesta.texto or "")


@dataclass
class ResultadoModelo:
    """Agregado de una corrida completa (o parcial) por modelo."""

    modelo: str
    registros: list[RegistroEvaluacion] = field(default_factory=list)
    error: str | None = None


def _archivo_esperado_desde_yaml(valor: object) -> str | None:
    if valor is None or valor == "":
        return None
    s = str(valor).strip()
    if not s or s == "~":
        return None
    return s


def cargar_dataset(ruta: Path) -> list[dict[str, object]]:
    """Carga y valida el YAML de preguntas (esquema mínimo)."""
    if not ruta.is_file():
        msg = f"No se encontro el dataset: {ruta}"
        raise FileNotFoundError(msg)
    with ruta.open(encoding="utf-8") as f:
        raiz = yaml.safe_load(f)
    if not isinstance(raiz, dict):
        msg = "El YAML debe ser un diccionario con clave 'preguntas'."
        raise ValueError(msg)
    items = raiz.get("preguntas")
    if not isinstance(items, list):
        msg = "Falta la lista 'preguntas'."
        raise ValueError(msg)
    filas: list[dict[str, object]] = []
    for i, p in enumerate(items, start=1):
        if not isinstance(p, dict):
            msg = f"Entrada {i}: se esperaba un diccionario."
            raise TypeError(msg)
        if "id" not in p or "texto" not in p or "categoria" not in p:
            msg = f"Entrada {i}: faltan claves requeridas (id, texto, categoria)."
            raise ValueError(msg)
        p_norm = {
            "id": int(p["id"]),
            "texto": str(p["texto"]),
            "categoria": str(p["categoria"]),
            "archivo_esperado": _archivo_esperado_desde_yaml(
                p.get("archivo_esperado", None)
            ),
        }
        filas.append(p_norm)
    if len(filas) < 20:
        msg = f"Se requieren al menos 20 preguntas; hay {len(filas)}."
        raise ValueError(msg)
    return filas


def _modelo_a_slug(nombre: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", nombre.strip()).strip("-")


def _bloque_pregunta(reg: RegistroEvaluacion) -> str:
    r = reg.respuesta
    nombre_arch = r.archivo_fuente.name if r.archivo_fuente else "—"
    arch_exp = reg.archivo_esperado
    if arch_exp:
        if r.archivo_fuente and r.archivo_fuente.name == arch_exp:
            nota = " (✅ coincide)"
        else:
            nota = " (no coincide con el esperado)"
    else:
        nota = " (n/a, sin referencia fija)"
    lineas = [
        f"### Pregunta {reg.indice_muestra} — {reg.texto_pregunta}",
        "",
        f"- **Categoría:** {reg.categoria}",
        f"- **Archivo esperado:** {arch_exp if arch_exp else '—'}",
        f"- **Archivo recuperado (top-1):** {nombre_arch}{nota}",
    ]
    if r.fuentes_bm25:
        lista_ctx = ", ".join(
            f"`{f.ruta.name}` ({f.score:.2f})" for f in r.fuentes_bm25
        )
        lineas.append(
            f"- **BM25 — archivos en contexto ({len(r.fuentes_bm25)}):** {lista_ctx}"
        )
    lineas.extend(
        [
            f"- **Score BM25 (top-1):** {r.score_recuperacion:.2f}",
            f"- **Latencia:** {r.latencia_ms} ms",
            "- **Respuesta:**",
            "",
        ]
    )
    cuerpo = "\n".join(lineas)
    # Citas en bloque: indentar cuerpo de respuesta
    texto = (r.texto or "").strip()
    if texto:
        bloque = "\n".join("> " + linea for linea in texto.splitlines())
        cuerpo += bloque + "\n"
    else:
        cuerpo += "> _(vacío)_\n"
    cuerpo += "\n"
    return cuerpo


def escribir_reporte(
    resultado: ResultadoModelo,
    ruta_salida: Path,
    fecha_informe: date,
) -> None:
    """Escribe el Markdown del informe o un breve error si :attr:`error` está definido."""
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    if resultado.error:
        cuerpo = (
            f"# Error — modelo {resultado.modelo}\n\n"
            f"**Fecha:** {fecha_informe.isoformat()}\n\n"
            f"```\n{resultado.error}\n```\n"
        )
        ruta_salida.write_text(cuerpo, encoding="utf-8")
        return

    regs = resultado.registros
    n = len(regs)
    if n == 0:
        lat_media = 0.0
    else:
        lat_media = sum(r.respuesta.latencia_ms for r in regs) / n

    con_exp = [r for r in regs if r.archivo_esperado]
    aciertos = sum(1 for r in con_exp if r.acierto_archivo is True)
    m = len(con_exp)
    con_sin_info = sum(1 for r in regs if r.es_respuesta_sin_informacion)
    tasa_sin = 0.0 if n == 0 else 100.0 * con_sin_info / n

    lineas: list[str] = [
        f"# Evaluación Q&A — {resultado.modelo}",
        "",
        f"- **Modelo:** `{resultado.modelo}`",
        f"- **Total de preguntas:** {n}",
        f"- **Fecha:** {fecha_informe.isoformat()}",
        f"- **Latencia promedio:** {lat_media:.0f} ms",
        f"- **Tasa de «{_FRASE_SIN_INFORMACION}»:** {tasa_sin:.1f} % "
        f"({con_sin_info} de {n})",
        "",
        "---",
        "",
    ]
    for reg in regs:
        lineas.append(_bloque_pregunta(reg))

    lineas.extend(
        [
            "## Resumen tabular",
            "",
            "| Métrica | Valor |",
            "| --- | --- |",
            f"| Total de preguntas | {n} |",
        ]
    )
    if m:
        lineas.append(
            f'| Aciertos en archivo (esperado definido) | {aciertos} / {m} |'
        )
    else:
        lineas.append("| Aciertos en archivo (esperado definido) | n/a (sin referencias) |")
    lineas.append(f'| Respuestas con «{_FRASE_SIN_INFORMACION}» | {con_sin_info} |')
    lineas.append("")
    ruta_salida.write_text("\n".join(lineas), encoding="utf-8")


def evaluar_modelo(
    modelo: str,
    pipeline: PipelineQa,
    preguntas: list[dict[str, object]],
) -> ResultadoModelo:
    """
    Ejecuta cada pregunta con ``responder(..., modelo=modelo)``.

    Ante :exc:`ModeloNoDisponibleError`, devuelve :class:`ResultadoModelo` con
    :attr:`error` y sin registros.
    """
    out = ResultadoModelo(modelo=modelo)
    for idx, p in enumerate(preguntas, start=1):
        texto = str(p["texto"])
        try:
            r = pipeline.responder(texto, modelo=modelo)
        except ModeloNoDisponibleError as exc:
            out.error = str(exc)
            return out
        arch_norm = _archivo_esperado_desde_yaml(p.get("archivo_esperado"))
        out.registros.append(
            RegistroEvaluacion(
                pregunta_id=int(p["id"]),
                texto_pregunta=texto,
                categoria=str(p["categoria"]),
                archivo_esperado=arch_norm,
                respuesta=r,
                indice_muestra=idx,
            )
        )
    return out


def parsear_argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evaluacion Q&A: ejecuta el dataset y genera informes por modelo."
    )
    p.add_argument(
        "--modelos",
        nargs="+",
        required=True,
        metavar="MODELO",
        help="Nombres de modelos Ollama (p. ej. llama3.1:8b gemma4:e2b)",
    )
    p.add_argument(
        "--dataset",
        type=Path,
        default=_DATASET_POR_DEFECTO,
        help="Ruta al YAML de preguntas (por defecto: tests/qa/preguntas_evaluacion.yml).",
    )
    p.add_argument(
        "--salida",
        type=Path,
        default=_SALIDA_POR_DEFECTO,
        help="Directorio base para los informes .md.",
    )
    p.add_argument(
        "--solo-pregunta",
        type=int,
        default=None,
        metavar="ID",
        dest="solo_pregunta",
        help="Solo ejecutar la pregunta con este id (depuracion).",
    )
    p.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha del informe en formato YYYY-MM-DD (por defecto: hoy).",
    )
    return p.parse_args()


def main() -> int:
    args = parsear_argumentos()
    try:
        preguntas = cargar_dataset(args.dataset)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Error al cargar el dataset: {exc}", file=sys.stderr)
        return 1

    if args.solo_pregunta is not None:
        filtrado = [x for x in preguntas if int(x["id"]) == args.solo_pregunta]
        if not filtrado:
            print(
                f"No hay pregunta con id {args.solo_pregunta} en {args.dataset}.",
                file=sys.stderr,
            )
            return 1
        preguntas = filtrado

    if args.fecha:
        try:
            fecha_d = date.fromisoformat(args.fecha)
        except ValueError:
            print(
                f"Fecha invalida: {args.fecha!r} (use YYYY-MM-DD).",
                file=sys.stderr,
            )
            return 1
    else:
        fecha_d = date.today()

    pipeline = construir_pipeline_por_defecto()
    code = 0
    for modelo in args.modelos:
        res = evaluar_modelo(modelo, pipeline, preguntas)
        slug = _modelo_a_slug(modelo) or "modelo"
        ruta = args.salida / f"{slug}__{fecha_d.isoformat()}.md"
        if res.error:
            print(f"Modelo {modelo!r} omitido: {res.error}")
            code = 1
        escribir_reporte(res, ruta, fecha_d)
        print(f"Informe generado: {ruta}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
