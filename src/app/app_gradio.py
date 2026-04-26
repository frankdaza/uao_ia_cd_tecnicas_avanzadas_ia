"""
Interfaz Q&A con Gradio: pregunta, modelo Ollama, prompt del sistema y trazabilidad.
"""

from __future__ import annotations

import gradio as gr

from src.qa.cliente_ollama import (
    ModeloNoDisponibleError,
    OllamaNoAccesibleError,
)
from src.qa.pipeline import (
    PROMPT_SISTEMA_DEFECTO,
    construir_pipeline_por_defecto,
)

_pipeline = construir_pipeline_por_defecto()


def manejar_pregunta(
    texto_pregunta: str,
    modelo_elegido: str,
    prompt_actual: str,
) -> tuple[str, str]:
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
    ruta = resultado.archivo_fuente
    archivo_txt = f"`{ruta}`" if ruta is not None else "*(sin documento; respuesta mínima)*"
    link_url = (
        f"[{resultado.source_url}]({resultado.source_url})"
        if (resultado.source_url or "").strip()
        else "*(ninguna)*"
    )
    meta = (
        f"**Archivo fuente:** {archivo_txt}  \n"
        f"**URL origen:** {link_url}  \n"
        f"**Score BM25:** {resultado.score_recuperacion:.2f}  \n"
        f"**Modelo:** `{resultado.modelo}` · **Latencia:** {resultado.latencia_ms} ms"
    )
    return resultado.texto, meta


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
                respuesta = gr.Markdown(label="Respuesta")
                metadatos = gr.Markdown(label="Trazabilidad")
                estado_recarga = gr.Markdown(
                    value="",
                    label="Recarga de corpus",
                )

        boton_preguntar.click(
            manejar_pregunta,
            inputs=[pregunta, modelo, prompt_textbox],
            outputs=[respuesta, metadatos],
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
    demo.launch()
