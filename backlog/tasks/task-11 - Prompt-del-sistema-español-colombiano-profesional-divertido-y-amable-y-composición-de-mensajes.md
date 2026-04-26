---
id: TASK-11
title: >-
  Prompt del sistema (español colombiano, profesional, divertido y amable) y
  composición de mensajes
status: Done
assignee: []
created_date: '2026-04-26 20:16'
updated_date: '2026-04-26 21:42'
labels:
  - llm
dependencies:
  - TASK-8
  - TASK-10
references:
  - .cursor/skills/qa-prompt-engineering/SKILL.md
ordinal: 1.953125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El requerimiento 7 del cliente exige que la UI permita **leer y editar** el prompt del sistema, y que el default sea **profesional, divertido y amable, en español colombiano**. Además, el requerimiento 6 obliga a que el LLM responda **solo** con base en el contenido del archivo `.md` recuperado y diga "No tengo información suficiente" si la respuesta no está.

## Objetivo

Implementar `src/qa/prompt.py` con:

1. Una constante exportable `PROMPT_SISTEMA_DEFECTO` con el tono solicitado.
2. Una función `componer_mensajes(prompt_sistema, contenido_md, pregunta) -> list[dict]` que arme el formato de mensajes para Ollama, inyectando el contenido completo del `.md` (sin chunking) en el rol `system` o como bloque de contexto.

## Diseño propuesto

```python
PROMPT_SISTEMA_DEFECTO: str = '''Eres "Lili", la asistente virtual oficial de la Fundación Valle del Lili. Hablas en español colombiano (parcero, con mucho cariño y profesionalismo, sin caer en localismos pesados).

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
'''

def componer_mensajes(
    prompt_sistema: str,
    contenido_md: str,
    pregunta: str,
    metadata_documento: dict | None = None,
) -> list[dict[str, str]]:
    contexto = (
        "CONTEXTO (extraído del archivo "
        f"{metadata_documento.get('source_url', 'sin URL') if metadata_documento else 'sin URL'}):\n\n"
        f"{contenido_md}\n\n"
        "Responde la pregunta del usuario usando solo este CONTEXTO."
    )
    return [
        {"role": "system", "content": prompt_sistema + "\n\n" + contexto},
        {"role": "user", "content": pregunta},
    ]
```

## Detalles técnicos

- **Inyección del .md completo**: el cuerpo (sin front matter) se incluye **completo y sin chunking** dentro del `system` (junto con el `prompt_sistema`). Documentar como decisión deliberada del MVP.
- **Reemplazo de placeholders**: opcional, pero útil — si el equipo decide usar `{contenido}` y `{source_url}` como tokens, sustituirlos antes de enviar.
- **Tono**: la frase "No tengo información suficiente" debe estar **literal** y aparecer en el prompt.
- El prompt es texto en español con tildes y eñes; los **identificadores** son ASCII puros (`PROMPT_SISTEMA_DEFECTO`, `componer_mensajes`).

## Tests

- `test_prompt_contiene_frase_clave`: el prompt por defecto contiene exactamente "No tengo información suficiente".
- `test_prompt_es_espanol_colombiano`: contiene al menos una marca contextual (p. ej. "parcero" o referencia a la Fundación Valle del Lili) y no contiene marcas de otros dialectos.
- `test_componer_mensajes_estructura`: devuelve lista con 2 elementos, roles `system` y `user`, y el contenido `.md` aparece dentro del system.
- `test_componer_mensajes_sin_truncar`: dado un `contenido_md` de 50000 caracteres, el system debe contenerlo completo (sin elipsis ni recorte).

## Identificadores ASCII

- `PROMPT_SISTEMA_DEFECTO`, `componer_mensajes`, `inyectar_contexto`, `validar_prompt`.

## Caso de negocio

El usuario debe poder leer/editar el prompt en la UI (task-13) y si lo daña, restaurar el por defecto. El equipo de la Fundación quiere consistencia de marca: tono colombiano, profesional y amable.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Existe constante PROMPT_SISTEMA_DEFECTO en src/qa/prompt.py
- [x] #2 PROMPT_SISTEMA_DEFECTO contiene literalmente la frase 'No tengo información suficiente'
- [x] #3 PROMPT_SISTEMA_DEFECTO menciona explícitamente Fundación Valle del Lili y tono español colombiano
- [x] #4 componer_mensajes(prompt, contenido_md, pregunta) devuelve lista con 2 dicts: roles 'system' y 'user'
- [x] #5 El contenido del .md se inyecta completo en el system (sin chunking, sin truncar)
- [x] #6 Test confirma que un .md de 50k caracteres queda intacto dentro del prompt compuesto
- [x] #7 Identificadores Python son ASCII puros (sin tildes ni eñes en nombres)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Crear src/qa/prompt.py con PROMPT_SISTEMA_DEFECTO
2) Iterar el texto del prompt con tono colombiano, profesional y divertido
3) Implementar componer_mensajes con dataclass opcional o dict
4) Validar que la frase No tengo información suficiente esté literal
5) Crear tests/qa/test_prompt.py con 4 tests definidos
6) Validar que un .md grande no se trunca
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agregó `src/qa/prompt.py` con `PROMPT_SISTEMA_DEFECTO` (Lili, Fundación Valle del Lili, español colombiano, reglas anti-alucinación, frase literal "No tengo información suficiente") y `componer_mensajes()` que concatena el prompt con el bloque CONTEXTO (URL opcional vía `metadata_documento` → `source_url`) y la pregunta en rol user. `tests/qa/test_prompt.py` cubre frase clave, tono, estructura y 50k caracteres sin truncar. `uv run pytest tests/qa/test_prompt.py` pasa.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 tests/qa/test_prompt.py existe y todos los tests pasan
- [x] #2 Sin import de chunking, embeddings ni librerías de RAG vectorial
- [x] #3 Comentarios en el módulo aclaran: 'fase 1 MVP: contexto = .md completo, sin chunking'
<!-- DOD:END -->
