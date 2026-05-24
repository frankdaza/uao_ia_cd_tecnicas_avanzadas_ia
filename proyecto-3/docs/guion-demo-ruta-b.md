# Guion demo en vivo — Ruta B (15 minutos)

Sustentacion **100 % practica** (sin diapositivas): codigo, terminal, dashboard OpenFang y Telegram en vivo.

Referencia: [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)

## Preparacion (antes de entrar al aula)

- [ ] OpenFang instalado y version anotada (`openfang --version`)
- [ ] `.env` con `OPENAI_API_KEY` y `TELEGRAM_BOT_TOKEN` (bot **distinto** al de `proyecto-2/`); ver [telegram-bot-setup.md](telegram-bot-setup.md)
- [ ] `./scripts/arrancar_dev.sh` (ingesta + Hand activo + getMe; o `./scripts/arrancar_dev.sh --sin-telegram` sin ping)
- [ ] Dashboard accesible: `http://127.0.0.1:4200`
- [ ] Pregunta de prueba preparada sobre protocolo FVL

## Minuto 0–2 — Contexto arquitectonico

- Mostrar arbol `proyecto-3/` vs `proyecto-2/` (Ruta A vs Ruta B en paralelo).
- Abrir `backlog/decisions/decision-8` y explicar alcance **OpenFang puro** (sin OLTP ni panel React).

## Minuto 2–5 — Memoria e ingesta

- Terminal: ejecutar o mostrar log de ingesta hacia Vector Store / KV.
- Dashboard OpenFang: [dashboard-openfang.md](dashboard-openfang.md) (memoria, sesiones, JSONL).
- Una frase: corpus desde `data/markdown/` y PDFs `data/taam/`.

## Minuto 5–8 — Hand autonomo

- Mostrar `openfang/hands/taam_lili_hand/HAND.toml` y `SKILL.md` (guardrails: no diagnostico).
- Terminal: estado del Hand (`taam_lili_hand` activo).
- Explicar schedule demo: `every_secs = 30` (recordatorio postoperatorio + evidencia en texto; en produccion futura podria usarse cron matutino segun decision-8).

## Minuto 8–12 — Prueba de fuego Telegram

- Profesor o publico envia mensaje al **bot Ruta B** desde su telefono.
- Narrar en tiempo real: Update → bridge OpenFang → RAG memoria → OpenAI → respuesta.
- Pregunta sugerida: cuidado postoperatorio o medicacion segun protocolo ingerido.
- Opcional: mensaje proactivo del Hand (~30 s con Hand activo) **o** disparo manual:
  `uv run python scripts/disparar_recordatorio_hand.py` (requiere sesion `telegram:{chat_id}` en JSONL).
- UC7 evidencia texto (demo): `uv run python scripts/disparar_recordatorio_hand.py --marcar-evidencia` luego `uv run python scripts/disparar_evidencia_hand.py --solo-simular` (o `--marcar-pendiente CHAT_ID` antes del segundo comando).
- Mostrar auditoria: `tail -n 3 openfang/data/audit/hand_recordatorio.jsonl` y `hand_evidencia.jsonl`.

## Minuto 12–14 — t-SNE (bonus)

- Abrir `analisis_tsne/notebooks/analisis_tsne.ipynb` (o PNG exportado).
- Explicar 2–3 clusters interpretados (dudas medicacion, alarma, agradecimiento).

## Minuto 14–15 — Cierre comparativo

- Una tabla verbal: Ruta A (`proyecto-2`) tiene OLTP + panel; Ruta B (`proyecto-3`) demuestra Agent OS + Hands.
- Limites explicitos: sin emparejamiento clinico ni evidencias multimedia en este MVP.

## Preguntas frecuentes del jurado

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Por que dos proyectos TAAM? | Ruta A evaluable con LangChain; Ruta B demuestra OpenFang sin romper decision-7. |
| ¿Donde esta el triage clinico? | En `proyecto-2/` (alertas Postgres); Ruta B solo memoria del OS y dashboard. |
| ¿Soberania de datos? | Documentar fallback Ollama; MVP acordado usa OpenAI como en proyecto-2. |

## Rollback si falla Telegram

1. Mostrar respuesta en dashboard OpenFang (mismo agente).
2. Mostrar ultimo JSONL de sesion en `OPENFANG_HOME` (ver [dashboard-openfang.md](dashboard-openfang.md)).
3. Explicar pin de version OpenFang y token del bot.
