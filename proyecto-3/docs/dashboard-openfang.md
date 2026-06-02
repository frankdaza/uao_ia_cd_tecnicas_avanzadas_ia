# Dashboard OpenFang e historial JSONL (UC4 parcial)

Guia operativa para **seguimiento de interacciones** en Ruta B (`proyecto-3/`): dashboard local del Agent OS y consulta de archivos JSONL bajo `OPENFANG_HOME`. Cubre **UC4** y consulta parcial de **UC9** segun [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md).

## Que demuestra y que no

| Incluido (UC4 parcial) | Fuera de alcance |
| --- | --- |
| Dashboard en `http://127.0.0.1:4200` | Panel React staff (`proyecto-2/`) |
| `openfang sessions --json` | Bandeja `alertas_triage` (Postgres Ruta A) |
| Lectura JSONL / SQLite en disco | Intervencion en hilo Telegram desde panel |
| Auditoria Hand (`audit/hand_*.jsonl`) | Pipeline t-SNE masivo (ver TASK-128 / `analisis_tsne/`) |

## Prerrequisitos

1. OpenFang **0.6.9** en PATH (`./scripts/instalar_openfang.sh`).
2. `.env` con `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `OPENFANG_HOME` (ver [`.env.example`](../.env.example)).
3. Arranque: `./scripts/arrancar_dev.sh` (dashboard + agente `bot_lili_taam` + Hand opcional).
4. Tráfico minimo: un mensaje en Telegram o copia del fixture de prueba (seccion [Extracto ficticio](#extracto-ficticio)).

Telegram en vivo: [telegram-bot-setup.md](telegram-bot-setup.md). Guion de sustentacion: [guion-demo-ruta-b.md](guion-demo-ruta-b.md).

## Dashboard (`http://127.0.0.1:4200`)

El puerto **4200** esta definido en [`openfang/openfang.toml`](../openfang/openfang.toml) (`api_listen`, verificado en pytest `test_dashboard_puerto_4200`).

Pasos genericos (la UI puede variar segun revision **0.6.9**; validar en tu instalacion):

1. Con `openfang status` en **running**, abrir `http://127.0.0.1:4200` en el navegador.
2. Localizar el agente **`bot_lili_taam`** (manifest en `openfang/agents/bot_lili_taam/agent.toml`).
3. Revisar secciones de **sesiones** y **memoria** (vector store / episodica) si el dashboard las expone.
4. Si Telegram falla en demo, usar el mismo agente desde el dashboard para enviar un turno de prueba (rollback del [guion demo](guion-demo-ruta-b.md)).

## CLI de sesiones

Convencion de sesion alineada con Ruta A:

```text
session_id = telegram:{chat_id}
```

Tras al menos un mensaje al bot:

```bash
export PATH="$HOME/.openfang/bin:$PATH"
export OPENFANG_HOME="$(pwd)/openfang/data"   # o valor de .env

openfang sessions --json
```

Busca entradas con prefijo `telegram:`. En documentacion y capturas **enmascara** el `chat_id` (ej. `telegram:****9001`); no pegues ids completos en backlog ni issues.

## Mapa de rutas bajo `OPENFANG_HOME`

Por defecto: `proyecto-3/openfang/data/` (gitignored; puede contener PII de demo).

| Ruta | Contenido |
| --- | --- |
| `data/openfang.db` | SQLite del kernel (memoria semantica, FTS5 si aplica) |
| `sessions/{chat_id}.jsonl` | Turnos episodicos por chat (adaptadores UC7, etc.) |
| `audit/hand_recordatorio.jsonl` | Eventos Hand recordatorio (`tipo: hand_recordatorio`) |
| `audit/hand_evidencia.jsonl` | Eventos Hand evidencia (`tipo: hand_evidencia`) |
| `kv/hand_evidencia/{chat_id}.json` | Estado pendiente evidencia (demo) |
| `logs/sessions.jsonl` | **Opcional:** agregado del daemon si existe tras trafico real |

### Descubrir archivos JSONL

```bash
find "$OPENFANG_HOME" -name '*.jsonl' | sort
```

Si no aparece ningun `.jsonl` tras chatear, revisa [Troubleshooting](#troubleshooting).

### Auditoria Hand (visible en demo UC4)

```bash
tail -n 5 "$OPENFANG_HOME/audit/hand_recordatorio.jsonl"
tail -n 5 "$OPENFANG_HOME/audit/hand_evidencia.jsonl"
```

Disparo manual sin esperar cron:

```bash
uv run python scripts/disparar_recordatorio_hand.py --solo-simular
uv run python scripts/disparar_evidencia_hand.py --marcar-pendiente 900001 --solo-simular
```

## Consulta con `jq`

Id ficticio de ejemplo (fixture de tests): **`telegram:900001`** → archivo `sessions/900001.jsonl`.

### Por archivo de chat

```bash
jq -c 'select(.session_id=="telegram:900001")' \
  "$OPENFANG_HOME/sessions/900001.jsonl"
```

### Todos los JSONL de sesion (excluye audit si nombras solo `sessions/`)

```bash
find "$OPENFANG_HOME/sessions" -name '*.jsonl' -print0 2>/dev/null \
  | xargs -0 -I{} jq -c 'select(.session_id=="telegram:900001")' {}
```

### Agregado del daemon (si existe)

```bash
if [[ -f "$OPENFANG_HOME/logs/sessions.jsonl" ]]; then
  jq -c 'select(.session_id=="telegram:900001")' \
    "$OPENFANG_HOME/logs/sessions.jsonl"
fi
```

### Alternativa Python (sin `jq`)

```bash
uv run python scripts/consultar_historial_sesion.py --session-id telegram:900001
```

Codigo compartido: `src/openfang/historial_jsonl.py` (reutilizado por recordatorio UC6 y TASK-128).

## Demo reproducible (sustentacion)

Checklist en tres pasos:

1. **Trafico de paciente de prueba**
   - Enviar un mensaje al bot Ruta B en Telegram, **o**
   - Copiar el fixture a runtime de prueba:
     ```bash
     mkdir -p "$OPENFANG_HOME/sessions"
     cp tests/fixtures/openfang_sesion_ejemplo.jsonl \
       "$OPENFANG_HOME/sessions/900001.jsonl"
     ```
2. **Listar sesion**
   ```bash
   openfang sessions --json | jq '.[] | select(.id? // .session_id? | startswith("telegram:"))'
   ```
   (Ajusta el filtro `jq` al esquema JSON que devuelva tu version de OpenFang.)
3. **Entrada de Hand visible**
   ```bash
   uv run python scripts/disparar_recordatorio_hand.py --solo-simular
   tail -n 1 "$OPENFANG_HOME/audit/hand_recordatorio.jsonl" | jq .
   ```

Integrar con minutos 2–5 y 8–12 de [guion-demo-ruta-b.md](guion-demo-ruta-b.md).

## Extracto ficticio

Basado en [`tests/fixtures/openfang_sesion_ejemplo.jsonl`](../tests/fixtures/openfang_sesion_ejemplo.jsonl) (sin PHI):

```json
{"session_id": "telegram:900001", "role": "user", "content": "Hola Bot Lili", "ts": "2026-05-23T14:00:00+00:00"}
{"session_id": "telegram:900001", "role": "assistant", "content": "Hola, en que puedo ayudarte con tu recuperacion?", "ts": "2026-05-23T14:00:05+00:00"}
```

Para evidencia del checklist FVL, pegar extractos anonimizados en [checklist-pruebas-chat-fvl.md](checklist-pruebas-chat-fvl.md) (seccion Evidencia).

## Troubleshooting

### `OPENFANG_HOME` inexistente o vacio

```bash
cd proyecto-3
mkdir -p openfang/data/sessions openfang/data/audit
export OPENFANG_HOME="$(pwd)/openfang/data"
# Anadir OPENFANG_HOME=./openfang/data en .env
./scripts/arrancar_dev.sh
```

Sin directorio runtime, OpenFang puede fallar al persistir sesiones o Hands.

### Dashboard no carga en `:4200`

- Comprobar salud: `curl -fsS http://127.0.0.1:4200/api/health` (o la URL de `OPENFANG_API_URL` en `.env`).
- Revisar firewall local.
- Reiniciar: `./scripts/detener_dev.sh` y `./scripts/arrancar_dev.sh`.
- Si `openfang stop` responde "No running daemon" pero el dashboard carga, el CLI esta usando otro `OPENFANG_HOME` (p. ej. `~/.openfang`). Usa siempre `./scripts/detener_dev.sh` o `source .env` antes de `openfang stop`.

### No hay archivos JSONL tras chatear

- Confirmar `OPENFANG_HOME` es el mismo que usa el daemon (`echo $OPENFANG_HOME` vs log de `arrancar_dev.sh`).
- Ejecutar `find "$OPENFANG_HOME" -name '*.jsonl'`.
- Consultar tambien SQLite: `ls -la "$OPENFANG_HOME/data/openfang.db"`.

### Privacidad

Misma regla que [telegram-bot-setup.md](telegram-bot-setup.md): no commitear `chat_id` completos, tokens ni capturas con datos reales de pacientes. Carpeta local opcional `docs/evidencia-chat-fvl/` (gitignored).

## Relacion con TASK-128 (t-SNE)

Para export masivo a Parquet y notebook, usar `analisis_tsne/src/extraer_jsonl.py` (TASK-128). Esta guia cubre **consulta manual** para demo UC4; no sustituye el pipeline de analitica.

## Referencias

- [README.md](../README.md) — variables y arranque
- [checklist-pruebas-chat-fvl.md](checklist-pruebas-chat-fvl.md) — pruebas RAG y evidencia de sesiones
- [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) — mapeo UC4/UC9
