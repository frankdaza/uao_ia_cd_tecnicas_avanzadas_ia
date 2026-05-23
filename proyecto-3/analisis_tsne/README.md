# Analisis t-SNE — Ruta Transversal B (Modulo 3)

Pipeline de ciencia de datos sobre el **historial de interacciones** persistido por OpenFang (JSONL espejo de sesiones y SQLite FTS5), segun la rubrica del Modulo 3.

## Flujo

```text
OpenFang runtime (JSONL + SQLite FTS5)
        │
        ▼
  extraer_jsonl.py  ──► DataFrame de transcripciones
        │
        ▼
  vectorizar.py     ──► embeddings OpenAI (text-embedding-3-small)
        │
        ▼
  analisis_tsne.ipynb ──► t-SNE / UMAP + plotly 2D/3D + interpretacion de clusters
```

## Requisitos

- Conversaciones acumuladas tras pruebas en Telegram (minimo ~20–30 sesiones recomendado para t-SNE estable).
- Variables en `proyecto-3/.env`: `OPENAI_API_KEY`, `OPENFANG_HOME`, `OPENAI_EMBEDDING_MODEL`.

## Ejecucion prevista

```bash
cd proyecto-3
uv sync
uv run python analisis_tsne/src/extraer_jsonl.py
uv run python analisis_tsne/src/vectorizar.py
uv run jupyter lab analisis_tsne/notebooks/
```

Salidas graficas sugeridas en `analisis_tsne/output/` (gitignored).

## Interpretacion esperada (informe)

Documentar en el informe final, por ejemplo:

- Cluster de **dudas sobre medicacion** o horarios.
- Cluster de **senales de alarma** o malestar.
- Cluster de **conversaciones cortas / agradecimiento**.
- Conversaciones **fallidas** o sin respuesta util del agente.

## Bonus rubrica

Aplicacion correcta de t-SNE o UMAP + analisis logico de clusters: hasta **+10 %** sobre la nota final.

## Referencias

- [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)
- [Actividad Modulo 3 — Ruta Transversal B](../../backlog/docs/actividades/Actividad%20del%20M%C3%B3dulo%203_%20Productizaci%C3%B3n,%20Despliegue%20Avanzado%20y%20Sistemas%20Ag%C3%A9nticos.md)
