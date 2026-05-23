# proyecto-3 — TAAM Bot Lili (Modulo 3, Ruta B)

Implementacion **paralela** del Bot posoperatorio TAAM usando **[OpenFang](https://www.openfang.sh/)** como Agent OS, canal **Telegram** y Hand autonomo **`taam_lili_hand`**, mas analitica opcional **t-SNE** (Ruta Transversal B).

> **No sustituye** a `proyecto-2/` (Ruta A LangChain + FastAPI, [decision-7](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md)) ni a `proyecto-1/` (M2). Ver [decision-8](../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md).

## Alcance MVP (OpenFang puro)

| Incluido | Excluido |
| --- | --- |
| Chat paciente con RAG sobre memoria del OS | PostgreSQL OLTP, panel React staff |
| Hand cron: recordatorios postoperatorio | Emparejamiento codigo paciente ↔ caso |
| Solicitud de evidencias en **texto** por Telegram | Evidencias foto/audio/video |
| Ingesta de corpus `data/markdown/` y PDFs TAAM | Recordatorios de citas por email |
| Notebook t-SNE sobre historial JSONL del OS | WhatsApp, N8N, webhook FastAPI via 2 |

## Requisitos

- **OpenFang:** instalacion del binario (ver `scripts/instalar_openfang.sh`).
- **Python 3.12.12** + **uv** (solo para ingesta y notebook t-SNE).
- **OpenAI API** (mismo proveedor que `proyecto-2/` para comparacion entre rutas).
- **Bot Telegram** dedicado (token distinto al de `proyecto-2/`).

## Configuracion rapida

```bash
cd proyecto-3
cp .env.example .env
# Editar OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, OPENFANG_HOME

# Instalar OpenFang (una vez)
./scripts/instalar_openfang.sh

# Entorno Python auxiliar
uv sync

# Ingesta corpus (cuando este implementado)
uv run python ingesta/indexar_corpus_openfang.py

# Arranque desarrollo
./scripts/arrancar_dev.sh
```

Dashboard OpenFang: `http://127.0.0.1:4200`

## Estructura

```text
proyecto-3/
  openfang/           # Config OS, Hands, datos runtime (gitignore)
  ingesta/            # Corpus workspace → memoria OpenFang
  analisis_tsne/      # Extraccion JSONL, embeddings, notebook t-SNE
  scripts/            # install y arranque
  docs/               # guion demo 15 min
```

## Rubrica Modulo 3 (Ruta B)

| Entregable | Ubicacion |
| --- | --- |
| Conocimiento corporativo ingerido | `ingesta/` + logs |
| `HAND.toml` activo | `openfang/hands/taam_lili_hand/` |
| Telegram en vivo | bridge en `openfang/openfang.toml` |
| Bonus t-SNE | `analisis_tsne/notebooks/` |

## Referencias

- [decision-8](../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)
- [doc-007 — Evaluacion OpenFang](../backlog/docs/doc-007%20-%20Evaluacion-OpenFang-Proyecto-2-TAAM.md)
- [Caso de Uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)
