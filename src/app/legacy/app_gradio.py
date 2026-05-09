"""
DEPRECADO — Este módulo fue la interfaz Gradio del proyecto (fase 1, módulo 1).
Ha sido reemplazado por el frontend React 19 + Vite 7 + shadcn/ui en `frontend/`
y el backend FastAPI + SSE en `src/api/`. Se conserva aquí como referencia
histórica y para eventual uso en scripts de evaluación batch.

Ver:
- doc-002: backlog/docs/doc-002 - Migracion-Frontend-React-Vite-Backend-FastAPI.md
- ADR: backlog/decisions/decision-2 - Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md

NO usar este módulo como entrypoint principal. Usar:
    uv run uvicorn src.api.main:app --reload   (backend)
    pnpm --dir frontend dev                    (frontend)

---

Interfaz Q&A con Gradio: pregunta, modelos Ollama y OpenAI, respuesta dual opcional.

Streaming token a token: Ollama y OpenAI cuando cada uno corre solo.
Con ambos motores activos y clave válida: primero se transmite la salida Ollama y después
la de OpenAI (una sola pasada BM25; dos llamadas al modelo secuencialmente).
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import gradio as gr

from src.qa.cliente_ollama import (
    MODELO_LLAMA_3_1_8B,
    MODELOS_OLLAMA_SOPORTADOS,
    ModeloNoDisponibleError,
    NUM_CTX_MAX,
    OllamaNoAccesibleError,
)
from src.qa.cliente_openai import (
    MODELOS_OPENAI_SOPORTADOS,
    ClaveApiOpenAiAusenteError,
    MODELO_OPENAI_GPT_4O_MINI,
    OpenAiClienteError,
)
from src.qa.pipeline import (
    PROMPT_SISTEMA_DEFECTO,
    RespuestaQa,
    construir_pipeline_por_defecto,
)

_PIPELINE = construir_pipeline_por_defecto()


def _valor_inicial_slider_num_ctx() -> float:
    """Alinea el slider (4096..NUM_CTX_MAX) con la config actual de Ollama."""
    n = int(_PIPELINE._cliente.configuracion.num_ctx)
    n = max(4096, min(n, NUM_CTX_MAX))
    return float(n)


def _max_tokens_openai_efectivo(limitar: bool, tokens: float | int) -> int | None:
    if not limitar:
        return None
    return max(1, int(tokens))

_CSS_UI = """
#bloque-respuesta-o, #bloque-respuesta-oa {
    min-height: 220px;
    padding: 1rem 1.25rem;
    border-radius: 12px;
    background: var(--block-background-fill);
    line-height: 1.55;
}
#bloque-respuesta-o h2, #bloque-respuesta-oa h2 { margin-top: 0.6rem; margin-bottom: 0.4rem; }
#bloque-respuesta-o ul, #bloque-respuesta-oa ul,
#bloque-respuesta-o ol, #bloque-respuesta-oa ol { margin: 0.4rem 0 0.6rem 1.2rem; }
#bloque-respuesta-o p, #bloque-respuesta-oa p { margin: 0.4rem 0; }
#bloque-respuesta-o code, #bloque-respuesta-oa code { padding: 0.1rem 0.35rem; border-radius: 4px; }
#bloque-metadatos-o, #bloque-metadatos-oa { font-size: 0.92rem; opacity: 0.92; line-height: 1.45; }
#bloque-aviso-dual { font-size: 0.9rem; opacity: 0.95; }
#estado-consulta { min-height: 1.5rem; }
"""


def _mensaje_configurar_openai() -> str:
    return (
        "Configura la variable **OPENAI_API_KEY** en el archivo **`.env`** en la raíz "
        "del proyecto y vuelve a iniciar la aplicación."
    )


def _tiene_clave_openai() -> bool:
    c = _PIPELINE.cliente_openai
    if c is None:
        return False
    return c.configuracion.tiene_api_key()


def _formatear_metadatos(resultado: RespuestaQa) -> str:
    pie_modelo = (
        f"**Modelo:** `{resultado.modelo}` · **Latencia:** {resultado.latencia_ms} ms"
    )
    if resultado.fuentes_bm25:
        bloques: list[str] = []
        for i, fuente in enumerate(resultado.fuentes_bm25, start=1):
            archivo_txt = f"`{fuente.ruta.name}`"
            url = (fuente.source_url or "").strip()
            link_url = f"[{url}]({url})" if url else "*(sin URL)*"
            titulo_esc = (fuente.titulo or "").strip() or "*(sin título)*"
            bloques.append(
                f"{i}. {archivo_txt} · *{titulo_esc}* · "
                f"BM25 **{fuente.score:.2f}** · {link_url}"
            )
        cuerpo = "**Documentos recuperados (orden BM25, enviados al modelo):**\n\n"
        cuerpo += "\n\n".join(bloques)
        return f"{cuerpo}\n\n---\n\n{pie_modelo}"

    ruta = resultado.archivo_fuente
    archivo_txt = (
        f"`{ruta}`" if ruta is not None else "*(sin documento; respuesta mínima)*"
    )
    link_url = (
        f"[{resultado.source_url}]({resultado.source_url})"
        if (resultado.source_url or "").strip()
        else "*(ninguna)*"
    )
    return (
        f"**Archivo fuente:** {archivo_txt}  \n"
        f"**URL origen:** {link_url}  \n"
        f"**Score BM25:** {resultado.score_recuperacion:.2f}  \n"
        f"{pie_modelo}"
    )


def manejar_pregunta(
    texto_pregunta: str,
    modelo_elegido: str,
    prompt_actual: str,
) -> tuple[str, str]:
    """Versión no-streaming (compatibilidad): solo Ollama."""
    if not (texto_pregunta or "").strip():
        return "Por favor escribe una pregunta.", ""
    try:
        resultado = _PIPELINE.responder(
            pregunta=texto_pregunta,
            modelo=modelo_elegido,
            prompt_sistema=prompt_actual,
        )
    except (OllamaNoAccesibleError, ModeloNoDisponibleError) as exc:
        return f"**{exc}**", ""
    return resultado.texto, _formatear_metadatos(resultado)


def manejar_pregunta_stream(
    texto_pregunta: str,
    modelo_elegido: str,
    prompt_actual: str,
) -> Iterator[tuple[str, str]]:
    """Solo Ollama en streaming (compatibilidad con versiones anteriores)."""
    if not (texto_pregunta or "").strip():
        yield "Por favor escribe una pregunta.", ""
        return

    acumulado = ""
    try:
        for parcial, final in _PIPELINE.responder_stream(
            pregunta=texto_pregunta,
            modelo=modelo_elegido,
            prompt_sistema=prompt_actual,
        ):
            acumulado = parcial
            if final is None:
                yield acumulado, ""
            else:
                yield final.texto, _formatear_metadatos(final)
    except (OllamaNoAccesibleError, ModeloNoDisponibleError) as exc:
        yield f"**{exc}**", ""


def manejar_consulta_combinada(
    texto_pregunta: str,
    prompt_actual: str,
    usar_ollama: bool,
    usar_openai: bool,
    modelo_ollama: str,
    modelo_openai: str,
    num_ctx_ollama: float,
    limitar_respuesta_openai: bool,
    max_tokens_respuesta_openai: float,
) -> Iterator[tuple[str, str, str, str, str, str]]:
    """
    ``(estado_global, resp_o, meta_o, resp_oa, meta_oa, aviso_dual)``.

    Con un solo motor activo, las columnas no usadas quedan en blanco.
    """
    max_completion_openai = _max_tokens_openai_efectivo(
        limitar_respuesta_openai,
        max_tokens_respuesta_openai,
    )

    vacio = (
        "",
        "",
        "",
        "",
        "",
        "",
    )
    if not (texto_pregunta or "").strip():
        yield "Por favor escribe una pregunta.", *vacio[1:]
        return

    if not usar_ollama and not usar_openai:
        yield (
            "*(Activa al menos un motor de generación: Ollama u OpenAI.)*",
            "",
            "",
            "",
            "",
            "",
        )
        return

    sin_clave = usar_openai and not _tiene_clave_openai()

    if usar_ollama:
        _PIPELINE._cliente.configuracion.num_ctx = int(num_ctx_ollama)

    # Solo Ollama con streaming
    if usar_ollama and not usar_openai:
        try:
            for parcial, final in _PIPELINE.responder_stream(
                pregunta=texto_pregunta,
                modelo=modelo_ollama,
                prompt_sistema=prompt_actual,
            ):
                if final is None:
                    yield "", parcial, "", "", "", ""
                else:
                    yield (
                        "",
                        final.texto,
                        _formatear_metadatos(final),
                        "",
                        "",
                        "",
                    )
        except (OllamaNoAccesibleError, ModeloNoDisponibleError) as exc:
            yield f"**{exc}**", "", "", "", "", ""
        return

    # Solo OpenAI con streaming token a token
    if usar_openai and not usar_ollama:
        if sin_clave:
            yield "", "", "", _mensaje_configurar_openai(), "", ""
            return
        try:
            for parcial, final in _PIPELINE.responder_openai_stream(
                texto_pregunta,
                modelo_openai=modelo_openai,
                prompt_sistema=prompt_actual,
                max_completion_tokens=max_completion_openai,
            ):
                if final is None:
                    yield "", "", "", parcial, "", ""
                else:
                    yield (
                        "",
                        "",
                        "",
                        final.texto,
                        _formatear_metadatos(final),
                        "",
                    )
        except (ClaveApiOpenAiAusenteError, OpenAiClienteError) as exc:
            yield "", "", "", f"**{exc}**", "", ""
        return

    # Ambos motores con clave: secuencial (Ollama luego OpenAI), streaming en cada uno
    aviso = (
        "*Esta consulta ejecuta **dos** llamadas a modelo (Ollama y OpenAI): "
        "coste y límites de velocidad se aplican por separado a cada una.*"
    )
    if sin_clave:
        try:
            for parcial, final in _PIPELINE.responder_stream(
                pregunta=texto_pregunta,
                modelo=modelo_ollama,
                prompt_sistema=prompt_actual,
            ):
                if final is None:
                    yield (
                        "",
                        parcial,
                        "",
                        _mensaje_configurar_openai(),
                        "",
                        aviso,
                    )
                else:
                    yield (
                        "",
                        final.texto,
                        _formatear_metadatos(final),
                        _mensaje_configurar_openai(),
                        "",
                        aviso,
                    )
        except (OllamaNoAccesibleError, ModeloNoDisponibleError) as exc:
            yield f"**{exc}**", "", "", _mensaje_configurar_openai(), "", aviso
        return

    ctx = _PIPELINE.preparar_contexto_inferencia(
        texto_pregunta,
        prompt_actual,
    )
    if ctx.vacio:
        t_bm25 = time.perf_counter()
        ps = ctx.prompt_sistema_usado
        latencia_ms = int((time.perf_counter() - t_bm25) * 1000)
        texto_base = "No tengo información suficiente"
        base_kw = {
            "texto": texto_base,
            "archivo_fuente": None,
            "source_url": "",
            "titulo": "",
            "score_recuperacion": 0.0,
            "latencia_ms": latencia_ms,
            "prompt_sistema_usado": ps,
            "fuentes_bm25": (),
        }
        r_o = RespuestaQa(modelo=modelo_ollama, **base_kw)
        r_oa = RespuestaQa(modelo=modelo_openai, **base_kw)
        yield "", r_o.texto, _formatear_metadatos(r_o), "", "", aviso
        yield (
            "",
            r_o.texto,
            _formatear_metadatos(r_o),
            r_oa.texto,
            _formatear_metadatos(r_oa),
            aviso,
        )
        return

    t_ollama = time.perf_counter()
    texto_o = ""
    meta_o = ""
    try:
        for parcial, final in _PIPELINE.stream_ollama_desde_contexto(
            ctx,
            modelo_ollama,
            t_ollama,
        ):
            if final is None:
                yield "", parcial, "", "", "", aviso
            else:
                texto_o = final.texto
                meta_o = _formatear_metadatos(final)
                yield "", texto_o, meta_o, "", "", aviso
    except (OllamaNoAccesibleError, ModeloNoDisponibleError) as exc:
        yield f"**{exc}**", "", "", "", "", aviso
        return

    t_openai = time.perf_counter()
    try:
        for parcial, final in _PIPELINE.stream_openai_desde_contexto(
            ctx,
            modelo_openai,
            t_openai,
            max_completion_tokens=max_completion_openai,
        ):
            if final is None:
                yield "", texto_o, meta_o, parcial, "", aviso
            else:
                yield (
                    "",
                    texto_o,
                    meta_o,
                    final.texto,
                    _formatear_metadatos(final),
                    aviso,
                )
    except (ClaveApiOpenAiAusenteError, OpenAiClienteError) as exc:
        yield "", texto_o, meta_o, f"**{exc}**", "", aviso


def restaurar_prompt() -> str:
    return PROMPT_SISTEMA_DEFECTO


def al_recargar_corpus() -> str:
    _PIPELINE.recuperador.recargar()
    return "Listo: índice BM25 recargado desde el directorio de Markdown."


def actualizar_columnas_motores(
    usar_ollama: bool,
    usar_openai: bool,
) -> tuple:
    """Visibilidad de columnas, selectores por motor y aviso de coste dual."""
    ambos = usar_ollama and usar_openai
    ver_o = usar_ollama
    ver_a = usar_openai
    return (
        gr.update(visible=ver_o),
        gr.update(visible=ver_a),
        gr.update(visible=ambos),
        gr.update(visible=ver_o),
        gr.update(visible=ver_a),
        gr.update(visible=ver_o),
        gr.update(visible=ver_a),
    )


def construir_demo() -> gr.Blocks:
    with gr.Blocks(title="Q&A Fundación Valle del Lili") as demo:
        gr.Markdown("# Asistente Q&A — Fundación Valle del Lili")
        gr.Markdown(
            "Pregúntale lo que quieras sobre la información pública del sitio "
            "[valledellili.org](https://valledellili.org/). Las respuestas se basan "
            "exclusivamente en el contenido descargado."
        )

        with gr.Row():
            with gr.Column(scale=2):
                pregunta = gr.Textbox(
                    label="Tu pregunta",
                    placeholder="Ej: ¿Cómo puedo agendar una cita?",
                    lines=3,
                )
                usar_ollama = gr.Checkbox(
                    value=True,
                    label="Usar Ollama (generación local)",
                )
                usar_openai = gr.Checkbox(
                    value=False,
                    label="Usar OpenAI (API en la nube)",
                )
                with gr.Row(visible=True) as fila_modelo_ollama:
                    modelo = gr.Dropdown(
                        choices=list(MODELOS_OLLAMA_SOPORTADOS),
                        value=MODELO_LLAMA_3_1_8B,
                        label="Modelo (Ollama)",
                        info=(
                            "Requiere Ollama en ejecución (`ollama serve`). "
                            "Si el modelo no está instalado: **`ollama pull`** seguido del nombre elegido."
                        ),
                    )
                with gr.Row(visible=True) as fila_num_ctx_ollama:
                    slider_num_ctx = gr.Slider(
                        minimum=4096,
                        maximum=NUM_CTX_MAX,
                        step=2048,
                        value=_valor_inicial_slider_num_ctx(),
                        label="Ventana num_ctx (Ollama)",
                        info=(
                            "Contexto efectivo hasta "
                            + str(NUM_CTX_MAX)
                            + " tokens. Mayor valor usa más RAM/VRAM."
                        ),
                    )
                with gr.Row(visible=False) as fila_modelo_openai:
                    modelo_openai_dd = gr.Dropdown(
                        choices=list(MODELOS_OPENAI_SOPORTADOS),
                        value=MODELO_OPENAI_GPT_4O_MINI,
                        label="Modelo (OpenAI)",
                        info=(
                            "Requiere OPENAI_API_KEY en `.env`. "
                            "Si ves error de límite (429), prueba **`gpt-4o-mini`**, espera unos segundos "
                            "y revisa el uso del plan en el panel de OpenAI (no es un fallo de esta app)."
                        ),
                    )
                with gr.Row(visible=False) as fila_tokens_openai:
                    limitar_tokens_openai = gr.Checkbox(
                        value=False,
                        label="Limitar largo de respuesta OpenAI (max_completion_tokens)",
                    )
                    max_tokens_respuesta_openai = gr.Slider(
                        minimum=256,
                        maximum=4096,
                        step=256,
                        value=1024,
                        label="Máx. tokens en la respuesta",
                    )
                with gr.Accordion("Prompt del sistema (editable)", open=False):
                    prompt_textbox = gr.Textbox(
                        value=PROMPT_SISTEMA_DEFECTO,
                        label="Edita el prompt y presiona Preguntar",
                        lines=14,
                    )
                    boton_restaurar = gr.Button("Restaurar prompt por defecto")
                with gr.Row():
                    boton_preguntar = gr.Button("Preguntar", variant="primary")
                    boton_recargar = gr.Button("Recargar corpus", variant="secondary")
            with gr.Column(scale=3):
                estado_consulta = gr.Markdown(
                    elem_id="estado-consulta",
                    label="Estado",
                )
                with gr.Row():
                    with gr.Column(visible=True) as col_ollama:
                        gr.Markdown("### Respuesta — Ollama")
                        respuesta_o = gr.Markdown(
                            label="Texto",
                            elem_id="bloque-respuesta-o",
                        )
                        metadatos_o = gr.Markdown(
                            label="Trazabilidad",
                            elem_id="bloque-metadatos-o",
                        )
                    with gr.Column(visible=False) as col_openai:
                        gr.Markdown("### Respuesta — OpenAI")
                        respuesta_oa = gr.Markdown(
                            elem_id="bloque-respuesta-oa",
                        )
                        metadatos_oa = gr.Markdown(
                            elem_id="bloque-metadatos-oa",
                        )
                aviso_dual = gr.Markdown(
                    visible=False,
                    elem_id="bloque-aviso-dual",
                    label="Aviso",
                )
                estado_recarga = gr.Markdown(
                    value="",
                    label="Recarga de corpus",
                )

        usar_ollama.change(
            actualizar_columnas_motores,
            inputs=[usar_ollama, usar_openai],
            outputs=[
                col_ollama,
                col_openai,
                aviso_dual,
                fila_modelo_ollama,
                fila_modelo_openai,
                fila_num_ctx_ollama,
                fila_tokens_openai,
            ],
        )
        usar_openai.change(
            actualizar_columnas_motores,
            inputs=[usar_ollama, usar_openai],
            outputs=[
                col_ollama,
                col_openai,
                aviso_dual,
                fila_modelo_ollama,
                fila_modelo_openai,
                fila_num_ctx_ollama,
                fila_tokens_openai,
            ],
        )

        boton_preguntar.click(
            lambda: gr.update(interactive=False, value="Pensando..."),
            outputs=[boton_preguntar],
        ).then(
            manejar_consulta_combinada,
            inputs=[
                pregunta,
                prompt_textbox,
                usar_ollama,
                usar_openai,
                modelo,
                modelo_openai_dd,
                slider_num_ctx,
                limitar_tokens_openai,
                max_tokens_respuesta_openai,
            ],
            outputs=[
                estado_consulta,
                respuesta_o,
                metadatos_o,
                respuesta_oa,
                metadatos_oa,
                aviso_dual,
            ],
        ).then(
            lambda: gr.update(interactive=True, value="Preguntar"),
            outputs=[boton_preguntar],
        )
        boton_restaurar.click(
            restaurar_prompt,
            outputs=[prompt_textbox],
        )
        boton_recargar.click(
            al_recargar_corpus,
            outputs=[estado_recarga],
        )
    return demo


demo: gr.Blocks = construir_demo()

if __name__ == "__main__":
    demo.launch(css=_CSS_UI)
