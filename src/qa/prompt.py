"""
Prompt de sistema y composición de mensajes para chat con Ollama.

Fase 1 (MVP): el contexto enviado al modelo es el cuerpo del archivo ``.md``
completo (sin chunking, sin RAG vectorial). Si el documento excede la ventana
``num_ctx`` del modelo, Ollama puede truncar; eso se documenta en el cliente
LLM, no en este módulo.
"""

from __future__ import annotations

_SIN_URL_ETIQUETA: str = "sin URL"

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

Formato de salida:
- Texto plano en español colombiano.
- Si listas servicios o pasos, usa viñetas con "-".
"""


def componer_mensajes(
    prompt_sistema: str,
    contenido_md: str,
    pregunta: str,
    metadata_documento: dict | None = None,
) -> list[dict[str, str]]:
    """
    Arma la lista ``messages`` para ``POST /api/chat`` (Ollama u otro API compatible).

    El contexto (Markdown completo) va en el mensaje con rol ``system``, junto con
    las instrucciones del ``prompt_sistema``, para fijar de una vez conducta y datos.
    """
    url = _SIN_URL_ETIQUETA
    if metadata_documento:
        url = str(metadata_documento.get("source_url", _SIN_URL_ETIQUETA) or _SIN_URL_ETIQUETA)
    contexto = (
        "CONTEXTO (extraído del archivo con URL "
        f"{url}):\n\n"
        f"{contenido_md}\n\n"
        "Responde la pregunta del usuario usando solo este CONTEXTO."
    )
    contenido_sistema = f"{prompt_sistema.rstrip()}\n\n{contexto}"
    return [
        {"role": "system", "content": contenido_sistema},
        {"role": "user", "content": pregunta},
    ]
