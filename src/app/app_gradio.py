"""
Interfaz Q&A con Gradio: pregunta, modelo Ollama, prompt del sistema y trazabilidad.

Soporta streaming token a token, indicador de carga en el botón Preguntar y
respuestas renderizadas como Markdown enriquecido.
"""

from __future__ import annotations

from collections.abc import Iterator

import gradio as gr

from src.qa.cliente_ollama import (
    ModeloNoDisponibleError,
    OllamaNoAccesibleError,
)
from src.qa.pipeline import (
    PROMPT_SISTEMA_DEFECTO,
    RespuestaQa,
    construir_pipeline_por_defecto,
)

_pipeline = construir_pipeline_por_defecto()

_CSS_UI = """
#bloque-respuesta {
    min-height: 220px;
    padding: 1rem 1.25rem;
    border-radius: 12px;
    background: var(--block-background-fill);
    line-height: 1.55;
}
#bloque-respuesta h2 { margin-top: 0.6rem; margin-bottom: 0.4rem; }
#bloque-respuesta ul, #bloque-respuesta ol { margin: 0.4rem 0 0.6rem 1.2rem; }
#bloque-respuesta p { margin: 0.4rem 0; }
#bloque-respuesta code { padding: 0.1rem 0.35rem; border-radius: 4px; }
#bloque-metadatos { font-size: 0.92rem; opacity: 0.92; }
"""


def _formatear_metadatos(resultado: RespuestaQa) -> str:
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
        f"**Modelo:** `{resultado.modelo}` · **Latencia:** {resultado.latencia_ms} ms"
    )


def manejar_pregunta(
    texto_pregunta: str,
    modelo_elegido: str,
    prompt_actual: str,
) -> tuple[str, str]:
    """Versión no-streaming (compatibilidad). Devuelve respuesta y metadatos."""
    if not (texto_pregunta or "").strip():
        return "Por favor escribe una pregunta.", ""
    try:
        resultado = _pipeline.responder(
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
    """Generador para Gradio: yield ``(texto_acumulado, metadatos_md)``.

    Mientras llegan tokens, los metadatos quedan vacíos. Al final se emite el
    texto completo y el bloque de trazabilidad. Si Ollama no responde o el
    modelo no existe, muestra el mensaje de error en el área de respuesta y
    deja los metadatos vacíos sin propagar excepciones a la UI.
    """
    if not (texto_pregunta or "").strip():
        yield "Por favor escribe una pregunta.", ""
        return

    acumulado = ""
    try:
        for parcial, final in _pipeline.responder_stream(
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


def restaurar_prompt() -> str:
    return PROMPT_SISTEMA_DEFECTO


def al_recargar_corpus() -> str:
    _pipeline.recuperador.recargar()
    return "Listo: índice BM25 recargado desde el directorio de Markdown."


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
                modelo = gr.Radio(
                    choices=["llama3.1:8b", "gemma4:e2b"],
                    value="llama3.1:8b",
                    label="Modelo (Ollama)",
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
                respuesta = gr.Markdown(
                    label="Respuesta",
                    elem_id="bloque-respuesta",
                )
                metadatos = gr.Markdown(
                    label="Trazabilidad",
                    elem_id="bloque-metadatos",
                )
                estado_recarga = gr.Markdown(
                    value="",
                    label="Recarga de corpus",
                )

        boton_preguntar.click(
            lambda: gr.update(interactive=False, value="Pensando..."),
            outputs=[boton_preguntar],
        ).then(
            manejar_pregunta_stream,
            inputs=[pregunta, modelo, prompt_textbox],
            outputs=[respuesta, metadatos],
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
