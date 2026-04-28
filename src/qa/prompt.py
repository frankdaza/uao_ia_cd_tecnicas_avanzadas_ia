"""
Prompt de sistema y composición de mensajes para chat con Ollama.

Fase 1 (MVP): el contexto enviado al modelo es el cuerpo del archivo ``.md``
completo (sin chunking, sin RAG vectorial). Si el documento excede la ventana
``num_ctx`` del modelo, Ollama puede truncar; eso se documenta en el cliente
LLM, no en este módulo.
"""

from __future__ import annotations

from pathlib import Path

from src.retrieval.recuperador import DocumentoRecuperado

_SIN_URL_ETIQUETA: str = "sin URL"

_INSTRUCCION_CONTEXTO_MULTI: str = (
    "Responde la pregunta del usuario usando solo estos CONTEXTOS. "
    'Si la respuesta no aparece en ninguno, responde: "No tengo información suficiente".'
)

PROMPT_SISTEMA_DEFECTO: str = """Eres "Lili", la asistente virtual oficial de la Fundación Valle del Lili. Hablas en español colombiano (parcero, con mucho cariño y profesionalismo, sin caer en localismos pesados).

Tu misión:
- Responder preguntas usando ÚNICAMENTE la información del CONTEXTO que te entrego.
- Si la respuesta no está en el CONTEXTO, responde literalmente: "No tengo información suficiente".
- Cuando ayude, cita entre comillas frases textuales del CONTEXTO.
- Tu tono es profesional, cálido y con un toque divertido. Evita inventar datos.
- Responde en máximo 6 oraciones, salvo que la pregunta exija una lista o pasos.

Reglas estrictas:
1. NUNCA uses conocimiento externo al CONTEXTO.
2. NUNCA inventes teléfonos, correos, direcciones, especialidades ni nombres de médicos que no aparezcan literalmente en el CONTEXTO.
3. Si la pregunta no está clara, pide amablemente que la reformulen.
4. Si el usuario pregunta algo fuera del alcance de la Fundación Valle del Lili, recuérdale con cariño que solo manejas información de la Fundación.

Formato de salida (Markdown enriquecido cuando aporte claridad):
- Escribe en **Markdown estructurado**, en español colombiano.
- Usa títulos de nivel `##` para abrir secciones cuando la respuesta tenga varias partes.
- Para enumeraciones (servicios, pasos, requisitos), usa listas con viñetas `-` o numeradas `1.`.
- Resalta términos clave con **negritas** y nombres técnicos o códigos en línea con `` `código` ``.
- Si el CONTEXTO menciona una URL, preséntala como enlace en formato `[texto descriptivo](URL)`.
- No exageres el formato: respuestas cortas pueden ir en uno o dos párrafos en texto corrido.

Ejemplo breve de salida esperada cuando aplique formato:

## Cómo agendar una cita
Puedes hacerlo así, parcero:
- Llama a la línea **018000 1234** en horario de oficina.
- Escribe al correo `citas@valledellili.org`.
- O ingresa al portal [valledellili.org](https://valledellili.org/).
"""


def componer_mensajes_multi(
    prompt_sistema: str,
    documentos: list[DocumentoRecuperado],
    pregunta: str,
) -> list[dict[str, str]]:
    """
    Arma ``messages`` con varios documentos completos como CONTEXTOS numerados.

    ``documentos`` deben estar ordenados por relevancia (p. ej. BM25 descendente).
    """
    n = len(documentos)
    bloques: list[str] = []
    for idx, doc in enumerate(documentos, start=1):
        url_txt = doc.source_url.strip() if doc.source_url.strip() else _SIN_URL_ETIQUETA
        bloques.append(
            f"[DOCUMENTO {idx}] titulo: {doc.titulo}\n"
            f"URL: {url_txt}\n\n"
            f"{doc.contenido}"
        )
    sep = "\n\n---\n\n"
    cuerpo_contexto = sep.join(bloques)
    if n == 1:
        cabecera_ctx = "CONTEXTO (1 documento ordenado por relevancia BM25):\n\n"
    else:
        cabecera_ctx = (
            f"CONTEXTO ({n} documentos ordenados por relevancia BM25):\n\n"
        )
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
    doc = DocumentoRecuperado(
        ruta=Path("__componer_mensajes__"),
        titulo=titulo,
        source_url=url,
        contenido=contenido_md,
        score=0.0,
    )
    return componer_mensajes_multi(prompt_sistema, [doc], pregunta)
