---
name: qa-prompt-engineering
description: Disena prompts zero-shot y anti-alucinacion para Q&A basado solo en contexto del corpus. Usar al implementar src/laboratorio/qa_legacy o al evaluar calidad de respuestas.
---

# Prompt engineering (Modulo 1)

> Mantener el mismo contenido en `.cursor/skills/qa-prompt-engineering/` y `.claude/skills/qa-prompt-engineering/`.

## Fuente del contexto

- El **CONTEXTO** del sistema debe armarse a partir de la **base documental en Markdown**: archivos bajo **`data/markdown/`** (texto del cuerpo tras el front matter), **o** a partir de los **chunks** en **`data/processed/`** si ya existen fragmentos con metadatos.
- Prioridad: usar los mismos textos que el usuario puede inspeccionar en el repo (los `.md` en `markdown/`) para trazabilidad y demo.

## Rol del sistema (plantilla conceptual)

- Instruir: responder **solo** con informacion presente en el **CONTEXTO** (Markdown consolidado o chunks recuperados).
- Si la respuesta no esta en el contexto: decir explicitamente que **no hay informacion suficiente** en los datos disponibles.
- Tono: espanol latinoamericano, claro y breve.
- Opcional: pedir citas o frases literales entre comillas cuando el contexto lo permita.

## Experimento (actividad)

- Probar variantes **zero-shot**: orden de instrucciones, formato (lista vs parrafo), restriccion de longitud.
- Registrar en el informe que variante se uso y por que.

## Pruebas

- Al menos **20** preguntas distintas alineadas al alcance definido en la investigacion inicial.
- Anotar fallos (alucinacion, omision, ambiguedad) para la seccion de resultados.

## Codigo

- Variables en espanol ASCII (`plantilla_sistema`, `contexto_usuario`); el texto del prompt puede llevar tildes dentro de las cadenas.
