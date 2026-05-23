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

- **OpenFang** **0.6.9** (binario pinneado; ver [release v0.6.9](https://github.com/RightNow-AI/openfang/releases/tag/v0.6.9) y `.openfang-version`).
- **SO:** macOS o Linux (x86_64 o arm64). Windows: usar el instalador oficial (`install.ps1` en [openfang.sh](https://openfang.sh/)); fuera del alcance de los scripts de este repo.
- **Python 3.12.12** + **uv** (solo para ingesta y notebook t-SNE).
- **OpenAI API** (mismo proveedor que `proyecto-2/` para comparacion entre rutas).
- **Bot Telegram** dedicado (token distinto al de `proyecto-2/`).

## OpenFang (Agent OS)

Version fijada en el repo: **0.6.9** (archivo [`.openfang-version`](.openfang-version)).

### Instalacion y verificacion

```bash
cd proyecto-3
chmod +x scripts/instalar_openfang.sh
./scripts/instalar_openfang.sh

# Si openfang no esta en PATH en esta sesion:
export PATH="$HOME/.openfang/bin:$PATH"

# Solo smoke (sin reinstalar):
./scripts/instalar_openfang.sh --verificar-only
openfang --version    # debe contener 0.6.9
openfang start --help
```

El script instala en `~/.openfang/bin/openfang`. Variables utiles:

| Variable | Uso |
| --- | --- |
| `OPENFANG_VERSION` | Override del pin (por defecto lee `.openfang-version`) |
| `OPENFANG_BIN` | Ruta absoluta al binario para verificacion o ejecucion |
| `OPENFANG_DOWNLOAD_URL` | Solo pruebas o espejo interno; no usar en produccion |

Dashboard local tras `openfang start`: `http://127.0.0.1:4200`

### Instalacion manual (si falla `curl`)

1. Identificar el target Rust de tu maquina (ej. `aarch64-apple-darwin` en Mac Apple Silicon).
2. Descargar el tarball del release pinneado, por ejemplo:
   `https://github.com/RightNow-AI/openfang/releases/download/v0.6.9/openfang-aarch64-apple-darwin.tar.gz`
3. Extraer y copiar el binario `openfang` a `~/.openfang/bin/` (o cualquier ruta en tu `PATH`).
4. Verificar: `export OPENFANG_BIN=/ruta/a/openfang` y `./scripts/instalar_openfang.sh --verificar-only`

Otros artefactos del mismo release: [v0.6.9 — assets](https://github.com/RightNow-AI/openfang/releases/tag/v0.6.9).

### Fallback Ollama (opcional, solo documentacion)

La **Ruta B** prioriza **OpenAI** segun [decision-8](../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md). Si en una version concreta del binario falla la integracion OpenAI nativa, se puede documentar en `openfang/openfang.toml` un proveedor local **Ollama** (`OLLAMA_BASE_URL`, por defecto `http://127.0.0.1:11434`). No es el camino principal de la demo ni se configura en esta tarea.

## Configuracion rapida

```bash
cd proyecto-3
cp .env.example .env
# Editar OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, OPENFANG_HOME
# Variables centralizadas en src/configuracion.py (pydantic-settings)

# Instalar OpenFang (una vez)
./scripts/instalar_openfang.sh
export PATH="$HOME/.openfang/bin:$PATH"

# Entorno Python auxiliar
uv sync

# Ingesta corpus (cuando este implementado)
uv run python ingesta/indexar_corpus_openfang.py

# Arranque desarrollo
./scripts/arrancar_dev.sh
```

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
