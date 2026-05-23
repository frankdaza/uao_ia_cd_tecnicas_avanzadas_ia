# Bot Telegram dedicado — Ruta B (OpenFang)

Guia para crear y operar el bot de **proyecto-3** (TAAM Ruta B). El token debe ser **distinto** al de [`proyecto-2/`](../../proyecto-2/) (Ruta A).

Referencia: [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)

## Por que un bot distinto

| Aspecto | Ruta A (`proyecto-2`) | Ruta B (`proyecto-3`) |
| --- | --- | --- |
| Runtime | FastAPI + LangChain | OpenFang Agent OS |
| Canal Telegram | **Webhook** HTTPS (`setWebhook`) | **Long polling** (`getUpdates`) del bridge nativo |
| Variable | `TELEGRAM_BOT_TOKEN` en `proyecto-2/.env` | `TELEGRAM_BOT_TOKEN` en `proyecto-3/.env` |
| Emparejamiento | `/start CODIGO` con OLTP | No aplica en MVP Ruta B |

Si reutilizas el **mismo token** en ambos proyectos, Telegram solo permite un modo activo (webhook o polling) y las respuestas fallan o se pierden updates.

## 1. Crear el bot en @BotFather

1. Abre Telegram y busca **@BotFather**.
2. Envia `/newbot`.
3. Nombre visible sugerido: `FVL Lili Ruta B Dev`.
4. Username sugerido: termina en `bot`, por ejemplo `fvl_lili_rutab_dev_bot`.
5. Copia el token que entrega BotFather (formato `123456789:AA...`).

## 2. Configurar `.env` en proyecto-3

```bash
cd proyecto-3
cp .env.example .env
```

Edita `.env` (no commitear):

```bash
TELEGRAM_BOT_TOKEN=<pega-tu-token-aqui>
OPENAI_API_KEY=<tu-clave-openai>
```

Verifica que **no** sea el mismo valor que en `proyecto-2/.env`.

## 3. Comandos en BotFather (`/setcommands`)

En @BotFather, elige tu bot → **Edit Bot** → **Edit Commands** y pega:

```text
start - Iniciar conversacion con Bot Lili (TAAM Ruta B)
help - Ayuda y limites del asistente
version - Version OpenFang y hand activo
```

### Como responde el bot

El menu de Telegram es solo **ayuda de UI**. Las respuestas las genera el agente **`bot_lili_taam`** ([`openfang/agents/bot_lili_taam/agent.toml`](../openfang/agents/bot_lili_taam/agent.toml)) via OpenFang:

| Comando | Comportamiento esperado |
| --- | --- |
| `/start` | Saludo como **Bot Lili**, seguimiento postoperatorio FVL, disclaimer (no diagnostico, urgencias) |
| `/help` | Limites del asistente: orientacion segun protocolos, sin cambiar tratamiento ni diagnosticar |
| `/version` | Puede citar version de OpenFang (`openfang --version`) y hand `taam_lili_hand`; no es handler fijo del bridge |

Mensajes de texto libre (p. ej. cuidados postoperatorios) siguen el mismo agente con RAG sobre memoria del OS.

## 4. Verificar token (sin arrancar OpenFang)

```bash
cd proyecto-3
chmod +x scripts/verificar_telegram_bot.sh
./scripts/verificar_telegram_bot.sh
```

Salida esperada: `OK: bot @tu_username_bot (id=...)`.

## 5. Arrancar OpenFang con bridge Telegram

```bash
export PATH="$HOME/.openfang/bin:$PATH"
set -a && source .env && set +a
./scripts/validar_openfang_config.sh
./scripts/arrancar_dev.sh
```

- Dashboard: `http://127.0.0.1:4200`
- Config canal: [`openfang/openfang.toml`](../openfang/openfang.toml) → `[channels.telegram]`, `default_agent = "bot_lili_taam"`, `allowed_users = []` (cualquier usuario en dev).

## 6. Prueba en vivo

1. Abre el bot en Telegram (enlace `t.me/<username>`).
2. Envia `/start` — debe responder **Bot Lili** con tono empatico y limites clinicos.
3. Envia `/help` — debe reiterar que no diagnostica ni sustituye valoracion medica.
4. Pregunta de prueba: *¿Que cuidados generales hay despues de una cirugia?* (si hay corpus ingerido).
5. En terminal:

```bash
openfang sessions --json
```

Busca una sesion con formato `telegram:{chat_id}`. En notas o capturas usa solo el id **enmascarado** (ver seccion Privacidad).

## 7. Troubleshooting

### Token invalido (prueba negativa)

En una **subshell** (no modifica tu `.env` real):

```bash
TELEGRAM_BOT_TOKEN='12345:token-invalido-de-prueba' ./scripts/verificar_telegram_bot.sh
```

Salida esperada: error con **401** o **Unauthorized** de la API de Telegram.

Si OpenFang arranca con token invalido, revisa logs del daemon: deben mencionar fallo de autenticacion con Telegram, no un crash silencioso.

### El bot no responde

- Confirma `openfang status` → running.
- Confirma `OPENAI_API_KEY` en `.env` (el agente usa OpenAI).
- No ejecutes `scripts/configurar_webhook_telegram.py` de **proyecto-2** contra este bot (conflicto polling/webhook).
- Reinicia: `openfang stop` y `./scripts/arrancar_dev.sh`.

### Polling vs webhook

- **Ruta B:** OpenFang hace **long polling** automaticamente; no necesitas tunel HTTPS para Telegram.
- **Ruta A:** requiere URL publica y `setWebhook` (ver [`proyecto-2/README.md`](../../proyecto-2/README.md)).

## 8. Privacidad en logs y documentacion

No pegues el `chat_id` completo en issues, backlog ni capturas de pantalla. Usa enmascaramiento (ultimos 4 digitos visibles):

```python
from src.privacidad import enmascarar_chat_id_telegram

enmascarar_chat_id_telegram(123456789)  # -> "*****6789"
```

Ejemplos en logs del doc:

| chat_id real | Mostrar en doc/log |
| --- | --- |
| `123456789` | `*****6789` |
| `42` | `****` |

## Referencias

- [README proyecto-3](../README.md)
- [Guion demo 15 min](guion-demo-ruta-b.md)
- [TASK-119 / openfang.toml](../../backlog/tasks/task-119%20-%20openfang.toml-config-real-modelo-OpenAI-memoria-bridge-Telegram-Hands.md)
