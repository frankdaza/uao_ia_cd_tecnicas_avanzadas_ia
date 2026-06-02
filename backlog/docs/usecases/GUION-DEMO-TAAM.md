# Guion de sustentacion TAAM (15 minutos)

Guion operativo extendido para la demo en vivo del Modulo 3. Resumen de casos de uso: [Caso de Uso TAAM - Bot Posoperatorio](Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md) (seccion 9). Semilla: `proyecto-2/scripts/sembrar_demo_taam.py` (TASK-114).

**Roles:** presentador (laptop), paciente (Telegram en telefono), opcional asistente (segundo dispositivo).

---

## Checklist pre-demo (15–30 min antes)

| Item | Comando / verificacion | OK |
|------|------------------------|-----|
| Stack Docker TAAM | `cd proyecto-2 && docker compose up -d` | API `:8001`, Postgres `:15433`, Qdrant `:6334` |
| Migraciones | `uv run alembic upgrade head` | Sin error |
| `.env` local | Copiar desde `.env.example`; **no** commitear secretos | `STAFF_JWT_SECRET`, `TELEGRAM_*`, `OPENAI_API_KEY` si usa RAG real; `RECORDATORIOS_JOB_HABILITADO=false` si no prueba recordatorios en vivo |
| Semilla demo | `uv run python -m scripts.sembrar_demo_taam` | Mensaje «Demo TAAM listo» |
| Ingesta RAG (opcional) | `uv run python -m scripts.sembrar_demo_taam --con-ingesta` | Requiere Qdrant + `OPENAI_API_KEY` |
| Webhook HTTPS | `uv run python -m scripts.configurar_webhook_telegram --url https://TU-TUNEL/.../api/integracion/telegram/webhook` | Telegram entrega updates |
| Frontend dev | `cd frontend && pnpm dev` (puerto **5174**) | Proxy `/api` → `:8001` |
| Health | `curl -sS http://127.0.0.1:8001/api/salud` | `{"estado":"ok","proyecto":"taam"}` |

**Tests vs demo en vivo:** los tests de API hacen **mock** de `invocar_agente` (sin llamadas OpenAI). La sustentacion con RAG/ingesta real si necesita `OPENAI_API_KEY`. No configure `MOCK_LLM` en producto; use mocks solo en pytest.

---

## Credenciales y datos ficticios (sin PHI)

| Rol | Email | Password (`.env.example`) |
|-----|-------|---------------------------|
| Admin catalogo | `admin@demo.taam` | `STAFF_DEMO_ADMIN_PASSWORD` |
| Asistente | `asistente@demo.taam` | `STAFF_DEMO_ASISTENTE_PASSWORD` |
| Clinico / seguimiento | `clinico@demo.taam` | `STAFF_DEMO_CLINICO_PASSWORD` |

| Entidad | Valor demo |
|---------|------------|
| Procedimiento | `COLE-LAP-001` — Colecistectomia laparoscopica (ficticio) |
| Caso A | `PAC-DEMO-001` — Ana Ficticia Lopez (`chat_id` ficticio `111111111` en BD para seguimiento; Telegram real tras `/start` + emparejamiento) |
| Caso B | `PAC-DEMO-002` — Bruno Ficticio Ruiz (codigo pendiente `DEMO2X`; placeholder `222222222` hasta emparejar) |
| PDF protocolo | `data/taam/demo/colecistectomia-protocolo-sintetico.pdf` |

---

## Tabla minuto a minuto (15 min)

| Min | Paso | Pantalla / terminal | Evidencia |
|-----|------|---------------------|-----------|
| 0–1 | Intro | Diapositiva o README: decision-7, diagrama Telegram → FastAPI → agente → PG/Qdrant | Separacion `proyecto-1` (M2) vs `proyecto-2` (TAAM) |
| 1–3 | UC-MVP-01 | Login `admin@demo.taam` → panel procedimientos: `COLE-LAP-001` con `indexacion_estado=ok` | `GET /api/admin/procedimientos` o UI admin |
| 3–5 | UC-MVP-02 | Login `asistente@demo.taam` → `/casos`: ver caso A y B; opcional crear caso y generar codigo; paciente `/start DEMO2X` en Telegram | Listado `vinculado_telegram` |
| 5–9 | UC-MVP-03 | Telefono: «¿Cuando puedo retomar caminatas leves?» luego «Tengo sangrado abundante en la herida» | Respuesta FAQ + escalamiento; log `POST /chat` o webhook |
| 9–11 | UC-MVP-04 | `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` o esperar job | Mensaje plantilla en Telegram |
| 11–14 | UC-MVP-05 | Login `clinico@demo.taam` → `/seguimiento`: alerta urgente caso A; abrir conversacion; **Marcar revisado** | Bandeja vacia de pendientes |
| 14–15 | Cierre | Matriz UC (doc TASK-97), riesgos PDF/plantillas, Fase 2 | — |

**Frases clave:** «Ruta A con tools tipadas», «HITL en urgente», «M2 institucional intacto en proyecto-1».

---

## Comandos de referencia (copiar en terminal)

```bash
# 1. Infra
cd proyecto-2
docker compose up -d

# 2. Esquema y semilla
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15433/taam'
uv run alembic upgrade head
uv run python -m scripts.sembrar_demo_taam

# 3. (Opcional) Vectores en Qdrant
uv run python -m scripts.sembrar_demo_taam --con-ingesta

# 4. API en primer plano (otra terminal)
uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001

# 5. Webhook (tunel HTTPS previo)
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_WEBHOOK_SECRET='...'
uv run python -m scripts.configurar_webhook_telegram \
  --url 'https://TU-TUNEL.example/api/integracion/telegram/webhook'

# 6. Frontend
cd frontend && pnpm dev
```

**Logs utiles durante UC-MVP-03:** terminal Uvicorn (`POST /api/integracion/telegram/webhook`, invocacion agente); evitar mostrar tokens en pantalla.

---

## Preguntas sugeridas al bot (Telegram)

1. «¿Cuando puedo retomar caminatas leves?» → severidad esperada: `info` (FAQ `caminata_postoperatoria`).
2. «Tengo sangrado abundante en la herida» → severidad esperada: `urgente` + alerta en panel (caso A ya tiene alerta sembrada para UC-MVP-05).

---

## Fallbacks si algo falla

| Problema | Accion rapida |
|----------|----------------|
| Webhook sin HTTPS | Probar emparejamiento con caso A ya vinculado; explicar limite Telegram |
| OpenAI / Qdrant caido | Respuestas FAQ siguen en JSON; RAG puede omitirse en intro |
| Semilla incompleta | Re-ejecutar `uv run python -m scripts.sembrar_demo_taam` (idempotente) |
| Sin telefono segundo rol | Presentador alterna pestaña staff y Telegram en el mismo dispositivo |

---

## Referencias

- [decision-7 — Arquitectura M3 TAAM](../../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md)
- [TASK-114 — Datos demo y guion](../../tasks/task-114%20-%20Datos-demo-FAQs-estructuradas-TAAM-y-guion-sustentación-15-min.md)
- `proyecto-2/README.md` — seccion **Demo en vivo**
