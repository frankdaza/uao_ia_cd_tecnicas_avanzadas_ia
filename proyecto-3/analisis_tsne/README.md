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

## Extraccion (`extraer_jsonl.py`)

Lee turnos bajo `OPENFANG_HOME` (JSONL en `sessions/` y opcional `logs/sessions.jsonl`) y complementa con filas episodicas de `data/openfang.db` si existen. Escribe `analisis_tsne/output/sesiones.parquet`.

| Columna | Descripcion |
| --- | --- |
| `session_id` | Ej. `telegram:900001` |
| `turno` | Entero 1..N por sesion (orden temporal) |
| `rol` | `user`, `assistant` o `system` |
| `texto` | Contenido del turno |
| `timestamp` | ISO-8601 UTC |
| `canal` | Ej. `telegram` |

Flags CLI:

| Flag | Efecto |
| --- | --- |
| `--openfang-home` | Override de `OPENFANG_HOME` |
| `--salida` | Ruta parquet (default `analisis_tsne/output/sesiones.parquet`) |
| `--incluir-audit` | Incluye `audit/hand_*.jsonl` |
| `--solo-jsonl` | No consulta SQLite |

Codigos de salida: `0` ok; `1` `sin_datos`; `2` `openfang_home_inexistente`. Si SQLite no aporta datos, el log incluye `fts5_ausente` y el script sigue con JSONL.

Demo sin Telegram: copiar el fixture de tests a runtime (ver [dashboard-openfang.md](../docs/dashboard-openfang.md)).

## Vectorizacion (`vectorizar.py`)

Lee `analisis_tsne/output/sesiones.parquet` (TASK-128) y genera:

| Artefacto | Descripcion |
| --- | --- |
| `vectores.npy` | Matriz `float32` shape `(N, D)` — un vector por unidad |
| `metadatos.parquet` | N filas alineadas por indice con `vectores.npy` |

Columnas de `metadatos.parquet`: `indice`, `session_id`, `canal`, `turno`, `rol`, `texto`, `modo`, `timestamp`.

**Modo sesion (default):** una fila por `session_id`; el texto embedido concatena turnos como `"{rol}: {texto}"` separados por salto de linea (orden por `turno`).

**Modo turno (`--por-turno`):** un embedding por fila del parquet de sesiones.

Flags CLI:

| Flag | Default | Efecto |
| --- | --- | --- |
| `--entrada` | `analisis_tsne/output/sesiones.parquet` | Parquet de entrada |
| `--salida-vectores` | `.../vectores.npy` | Salida numpy |
| `--salida-metadatos` | `.../metadatos.parquet` | Metadatos alineados |
| `--por-turno` | off | Embedding por turno en lugar de por sesion |
| `--tam-lote` | `32` | Tamano de lote para la API |
| `--modelo` | `OPENAI_EMBEDDING_MODEL` | Override del modelo |

Codigos de salida: `0` ok; `1` stderr `sin_datos` (parquet vacio o sin textos; **no** llama a la API).

Reintentos: hasta 3 llamadas con backoff exponencial (`1s`, `2s`) ante errores transitorios de la API.

Logica en `src/openfang/vectorizacion_tsne.py`; el script CLI es un envoltorio delgado.

## Ejecucion prevista

```bash
cd proyecto-3
uv sync
uv run python analisis_tsne/src/extraer_jsonl.py
uv run python analisis_tsne/src/vectorizar.py
uv run jupyter lab analisis_tsne/notebooks/
```

Salidas en `analisis_tsne/output/` (gitignored salvo `.gitkeep`).

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
