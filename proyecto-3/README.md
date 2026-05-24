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
- **Bot Telegram** dedicado (token distinto al de `proyecto-2/`). Guia: [`docs/telegram-bot-setup.md`](docs/telegram-bot-setup.md).

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

### Configuracion OpenFang (`openfang.toml`)

El archivo versionado [`openfang/openfang.toml`](openfang/openfang.toml) sigue el esquema **OpenFang 0.6.9**: `[default_model]`, `[memory]`, `[channels.telegram]`. Los secretos van en `.env` (`OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`); nunca en el TOML.

| Variable | Rol |
| --- | --- |
| `OPENFANG_HOME` | Directorio runtime (SQLite, JSONL). Por defecto `./openfang/data` relativo a `proyecto-3/`. |
| `OPENAI_API_KEY` | Clave para `[default_model]` (`api_key_env = "OPENAI_API_KEY"`) y embeddings de memoria. |
| `TELEGRAM_BOT_TOKEN` | Token del bot dedicado Ruta B (`bot_token_env` en `[channels.telegram]`). |

Al arrancar, los scripts copian `openfang/openfang.toml` → `{OPENFANG_HOME}/config.toml` y enlazan `openfang/agents/*` → `{OPENFANG_HOME}/agents/` (el bridge Telegram resuelve `default_agent` desde ahi).

### Flujo unico de desarrollo

Un solo comando sustituye validacion manual, `openfang start`, ingesta, activacion del Hand y ping Telegram:

```bash
cd proyecto-3
cp .env.example .env          # una vez: OPENAI_API_KEY, TELEGRAM_BOT_TOKEN
./scripts/instalar_openfang.sh
export PATH="$HOME/.openfang/bin:$PATH"
uv sync
./scripts/arrancar_dev.sh
```

| Flag | Efecto |
| --- | --- |
| *(ninguno)* | Arranque completo + `verificar_telegram_bot.sh` (getMe) |
| `--sin-telegram` | Omite verificacion del bot (util sin token o en CI local) |
| `--help` | Ayuda de opciones |

El script exige `.env`, hace healthcheck en `GET /api/health`, ejecuta ingesta con `--permitir-db-en-vivo`, activa `taam_lili_hand` y deja el daemon corriendo al terminar con exito. Si lo interrumpes con Ctrl+C **mientras** el script aun ejecuta y el daemon lo inicio aqui, lo detiene. Tras ver `=== Listo ===`, Ctrl+C **no** para el daemon (sigue en segundo plano en el puerto API). La ingesta completa puede tardar varios minutos y consume API de embeddings.

**Detener el entorno dev** (Hand + daemon con el mismo `OPENFANG_HOME` que `.env`):

```bash
cd proyecto-3
./scripts/detener_dev.sh
```

Equivalente manual (si `openfang stop` sin `.env` dice "No running daemon"):

```bash
cd proyecto-3
export PATH="$HOME/.openfang/bin:$PATH"
set -a && source .env && set +a
[[ "${OPENFANG_HOME}" != /* ]] && OPENFANG_HOME="$(cd "$(pwd)" && cd "${OPENFANG_HOME}" && pwd)"
export OPENFANG_HOME
openfang hand deactivate taam_lili_hand 2>/dev/null || true
openfang stop
```

Validacion solo de TOML (sin daemon): `./scripts/validar_openfang_config.sh`.

**Agente y Hand (no van en `openfang.toml`):**

- Agente corporativo: manifest [`openfang/agents/bot_lili_taam/agent.toml`](openfang/agents/bot_lili_taam/agent.toml) → `openfang agent spawn ...`
- Hand autonomo: [`openfang/hands/taam_lili_hand/`](openfang/hands/taam_lili_hand/) → `openfang hand install` / `openfang hand activate taam_lili_hand` (schedule demo: **`every_secs = 30`** en `HAND.toml`; desactivar fuera de pruebas para no consumir API)

```mermaid
flowchart LR
  paciente[Paciente Telegram]
  bridge["channels.telegram"]
  agente[bot_lili_taam]
  memoria["Memoria OS SQLite + embeddings"]
  hand[taam_lili_hand every 30s]
  openai[OpenAI API]

  paciente --> bridge
  bridge --> agente
  agente --> memoria
  agente --> openai
  hand --> bridge
  hand --> agente
```

**Sesiones:** convencion alineada con Ruta A: `session_id` = `telegram:{chat_id}` (entero del chat de Telegram). OpenFang la asigna en runtime; verificar con `openfang sessions --json` tras un mensaje de prueba. Ver [`docs/telegram-bot-setup.md`](docs/telegram-bot-setup.md) y seguimiento UC4 en [`docs/dashboard-openfang.md`](docs/dashboard-openfang.md).

**Telegram (BotFather, comandos, prueba en vivo):**

```bash
./scripts/arrancar_dev.sh             # flujo completo (incluye getMe)
./scripts/verificar_telegram_bot.sh   # solo getMe, sin arrancar el resto
```

### Fallback Ollama (si falla OpenAI nativo en demo)

La **Ruta B** prioriza **OpenAI** segun [decision-8](../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md). Si `openfang start` no conecta con OpenAI, sustituir temporalmente `[default_model]` en `openfang/openfang.toml`:

```toml
[default_model]
provider = "ollama"
model = "llama3.2:latest"
base_url = "http://127.0.0.1:11434"
api_key_env = ""
```

Asegurar `ollama serve` y el modelo descargado. Variable auxiliar en `.env.example`: `OLLAMA_BASE_URL`.

## Configuracion rapida

```bash
cd proyecto-3
cp .env.example .env
# Editar OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, OPENFANG_HOME
# Variables centralizadas en src/configuracion.py (pydantic-settings)

./scripts/instalar_openfang.sh
export PATH="$HOME/.openfang/bin:$PATH"
uv sync
./scripts/arrancar_dev.sh    # flujo unico: ver seccion anterior
```

Pasos manuales opcionales (depuracion):

```bash
uv run python ingesta/indexar_corpus_openfang.py --dry-run --limite 5
uv run python ingesta/indexar_corpus_openfang.py --solo-markdown --limite 20
uv run python scripts/contar_memorias_semanticas.py --exigir-ingesta
```

Detalle de flags y memoria SQLite: [`ingesta/README.md`](ingesta/README.md).

**Pruebas unitarias (TASK-132):** ingesta, extraccion JSONL, vectorizacion con mocks, guardrails y Hand; sin `OPENAI_API_KEY` real:

```bash
cd proyecto-3 && uv run pytest -q
cd proyecto-3 && uv run ruff check src ingesta analisis_tsne tests
```

**Pruebas chat RAG (TASK-122):** checklist manual [`docs/checklist-pruebas-chat-fvl.md`](docs/checklist-pruebas-chat-fvl.md); tests estaticos `uv run pytest tests/test_prompt_bot_lili.py tests/test_checklist_chat_fvl.py tests/test_sincronizar_prompt_agente.py`.

**Seguimiento UC4 (TASK-127):** guia [`docs/dashboard-openfang.md`](docs/dashboard-openfang.md); `uv run python scripts/consultar_historial_sesion.py --session-id telegram:900001`; tests `uv run pytest tests/test_dashboard_openfang_doc.py tests/openfang/test_historial_jsonl.py -q`.

**Pruebas Hand (TASK-123 / TASK-124 / TASK-125):** manifesto + UC6 recordatorio + UC7 evidencia texto; `uv run pytest tests/test_hand_taam_lili.py tests/hand/test_recordatorio_postop.py tests/hand/test_requerir_evidencia.py -q`. Disparo manual: `uv run python scripts/disparar_recordatorio_hand.py --solo-simular`; evidencia: `uv run python scripts/disparar_evidencia_hand.py --marcar-pendiente CHAT_ID --solo-simular`.

**Arranque dev (TASK-131):** `uv run pytest tests/test_arrancar_dev.py -q` (contrato de `arrancar_dev.sh` y `detener_dev.sh`; E2E con OpenFang es manual).

## Estructura

```text
proyecto-3/
  openfang/           # Config OS, Hands, datos runtime (gitignore)
  ingesta/            # Corpus workspace → memoria OpenFang
  analisis_tsne/      # Extraccion JSONL, embeddings, notebook t-SNE
  scripts/            # install y arranque
  docs/               # guion demo, telegram-bot-setup, dashboard-openfang, checklist FVL
  src/openfang/       # lectura JSONL historial (UC4, TASK-128)
  src/prompts/        # validacion estatica system prompt y HAND.toml
  src/hand/           # adaptadores testeables UC6 recordatorio y UC7 evidencia (TASK-124, TASK-125)
```

## Ruta A vs Ruta B

Implementacion **paralela** en el mismo workspace; no mezclar runtimes ni tokens Telegram.

| Tema | [`proyecto-2/`](../proyecto-2/) (Ruta A) | `proyecto-3/` (Ruta B) |
| --- | --- | --- |
| ADR | [decision-7](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) | [decision-8](../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) |
| Stack | LangChain + FastAPI + Postgres + Qdrant + React staff | OpenFang + Hand + memoria OS + ingesta Python |
| Telegram | Webhook en API `:8001` | Bridge nativo OpenFang |
| Panel / OLTP | Si (casos, alertas, emparejamiento) | No (dashboard `:4200` + JSONL) |
| Demo 15 min | [GUION-DEMO-TAAM](../backlog/docs/usecases/GUION-DEMO-TAAM.md) | [`docs/guion-demo-ruta-b.md`](docs/guion-demo-ruta-b.md) |
| Guia arquitectura | [doc-004](../backlog/docs/doc-004%20-%20Arquitectura-M3-Bot-Posoperatorio-TAAM.md) | [doc-008](../backlog/docs/doc-008%20-%20Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md) |

Detalle ampliado: [doc-008 §2](../backlog/docs/doc-008%20-%20Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md).

## Rubrica Modulo 3 (Ruta B)

| Entregable | Ubicacion |
| --- | --- |
| Conocimiento corporativo ingerido | `ingesta/` + logs |
| `HAND.toml` activo | `openfang/hands/taam_lili_hand/` |
| Telegram en vivo | `[channels.telegram]` en `openfang/openfang.toml` |
| Bonus t-SNE | `analisis_tsne/notebooks/` |

## Referencias

- [m-1 — Milestone Ruta B](../backlog/milestones/m-1%20-%20taam-ruta-b-openfang.md) (tasks 117–133, cierre documental TASK-133)
- [decision-8](../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) · [decision-7 Ruta A](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md)
- [doc-008 — Arquitectura M3 Ruta B](../backlog/docs/doc-008%20-%20Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md) · [doc-004 Ruta A](../backlog/docs/doc-004%20-%20Arquitectura-M3-Bot-Posoperatorio-TAAM.md)
- [doc-007 — Evaluacion OpenFang](../backlog/docs/doc-007%20-%20Evaluacion-OpenFang-Proyecto-2-TAAM.md)
- [Guion demo 15 min (Ruta B)](docs/guion-demo-ruta-b.md)
- [Caso de Uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)
