# Ingesta — corpus workspace → memoria OpenFang

Scripts auxiliares en Python para cargar el conocimiento corporativo en el **Vector Store** y **Structured KV** del agente OpenFang (requisito Ruta B, Modulo 3).

## Fuentes de datos

| Origen | Ruta workspace | Contenido |
| --- | --- | --- |
| Corpus Markdown M1/M2 | `data/markdown/` | Paginas institucionales con front matter YAML |
| Protocolos TAAM (PDF) | `data/taam/` | Recomendaciones postoperatorias por procedimiento |

Resolver la raiz del workspace con `UAO_WORKSPACE_ROOT` o subir dos niveles desde `proyecto-3/` hasta la raiz del repositorio.

## Script principal (placeholder)

```bash
cd proyecto-3
uv sync
uv run python ingesta/indexar_corpus_openfang.py
```

`indexar_corpus_openfang.py` debe (en implementacion futura):

1. Leer archivos `.md` y PDFs aplicables.
2. Fragmentar texto (tamano de chunk acorde a limites del OS).
3. Invocar la API o CLI de OpenFang para insertar en memoria semantica.
4. Opcional: escribir metadatos ligeros en Structured KV (tipo procedimiento, titulo, fuente).

## Verificacion rubrica

- Pregunta de prueba en Telegram sobre contenido conocido del corpus (p. ej. cuidados genericos FVL).
- Log de ingesta sin errores criticos.

## Referencias

- [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)
- [markdown-knowledge-base](../../.cursor/skills/markdown-knowledge-base/SKILL.md) (convencion `data/markdown/`)
