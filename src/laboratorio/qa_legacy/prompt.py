"""
Prompt de sistema y composición de mensajes para chat con Ollama.

Fase 1 (MVP): el contexto enviado al modelo es el cuerpo del archivo ``.md``
completo (sin chunking, sin RAG vectorial). Si el documento excede la ventana
``num_ctx`` del modelo, Ollama puede truncar; eso se documenta en el cliente
LLM, no en este módulo.
"""

from __future__ import annotations

from pathlib import Path

from src.agentes import prompt_institucional
from src.laboratorio.qa_legacy.documento_contexto import DocumentoContexto

PROMPT_SISTEMA_DEFECTO: str = prompt_institucional.PROMPT_SISTEMA_DEFECTO

_SIN_URL_ETIQUETA: str = "sin URL"

_INSTRUCCION_CONTEXTO_MULTI: str = (
    "Responde la pregunta del usuario usando solo estos CONTEXTOS. "
    'Si la respuesta no aparece en ninguno, responde: "No tengo información suficiente".'
)


def componer_mensajes_multi(
    prompt_sistema: str,
    documentos: list[DocumentoContexto],
    pregunta: str,
) -> list[dict[str, str]]:
    """
    Arma ``messages`` con varios documentos completos como CONTEXTOS numerados.

    ``documentos`` deben estar ordenados por relevancia (mejor primero).
    """
    n = len(documentos)
    bloques: list[str] = []
    for idx, doc in enumerate(documentos, start=1):
        url_txt = (
            doc.source_url.strip() if doc.source_url.strip() else _SIN_URL_ETIQUETA
        )
        bloques.append(
            f"[DOCUMENTO {idx}] titulo: {doc.titulo}\nURL: {url_txt}\n\n{doc.contenido}"
        )
    sep = "\n\n---\n\n"
    cuerpo_contexto = sep.join(bloques)
    if n == 1:
        cabecera_ctx = "CONTEXTO (1 documento ordenado por relevancia):\n\n"
    else:
        cabecera_ctx = f"CONTEXTO ({n} documentos ordenados por relevancia):\n\n"
    contexto = f"{cabecera_ctx}{cuerpo_contexto}\n\n{_INSTRUCCION_CONTEXTO_MULTI}"
    contenido_sistema = f"{prompt_sistema.rstrip()}\n\n{contexto}"
    return [
        {"role": "system", "content": contenido_sistema},
        {"role": "user", "content": pregunta},
    ]


def componer_mensajes(
    prompt_sistema: str,
    contenido_md: str,
    pregunta: str,
    metadata_documento: dict | None = None,
) -> list[dict[str, str]]:
    """
    Arma la lista ``messages`` para ``POST /api/chat`` (Ollama u otro API compatible).

    Compatibilidad: un solo documento vía :func:`componer_mensajes_multi`.
    """
    meta = metadata_documento or {}
    titulo = str(meta.get("titulo", "") or "")
    url = str(meta.get("source_url", "") or "")
    doc = DocumentoContexto(
        ruta=Path("__componer_mensajes__"),
        titulo=titulo,
        source_url=url,
        contenido=contenido_md,
        score=0.0,
    )
    return componer_mensajes_multi(prompt_sistema, [doc], pregunta)
