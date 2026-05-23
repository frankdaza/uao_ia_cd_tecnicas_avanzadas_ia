# Skill: taam_lili_hand — Bot Lili postoperatorio (TAAM)

Hand autonomo del **Agent OS OpenFang** para la Fundacion Valle del Lili. Complementa el chat reactivo (`bot_lili_taam`) con acciones programadas por Telegram.

## Casos de uso (Ruta B)

| UC | Capacidad HAND | Playbook |
| --- | --- | --- |
| UC6 Recordatorio postoperatorio | `recordatorio_postoperatorio` | [`prompts/recordatorio_postop.md`](prompts/recordatorio_postop.md) |
| UC7 Evidencias (solo texto MVP) | `requerir_evidencia_texto` | [`prompts/requerir_evidencia.md`](prompts/requerir_evidencia.md) |

Chat reactivo (UC8) usa [`prompts/system.md`](prompts/system.md) sincronizado a `openfang/agents/bot_lili_taam/agent.toml` (`scripts/sincronizar_prompt_agente.py`, TASK-122).

## Schedule (demo)

En [`HAND.toml`](HAND.toml):

- `every_secs = 30` — disparo cada 30 segundos para pruebas y sustentacion en vivo (sin esperar cron diario).
- `tz = "America/Bogota"`.

**Coste:** mas ticks implican mas llamadas al modelo; desactivar el Hand cuando no se este probando (`openfang hand deactivate taam_lili_hand` o equivalente en la version instalada).

**Futuro / produccion:** [decision-8](../../../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) sugiere recordatorio matutino via cron; no forma parte del manifesto versionado actual.

## Operacion

```bash
cd proyecto-3/openfang   # o desde proyecto-3 con ruta al Hand
openfang hand install hands/taam_lili_hand
openfang hand activate taam_lili_hand
openfang hand list
```

- **Canal por defecto:** Telegram (`[channel].default`).
- **Sesiones:** `session_id` = `telegram:{chat_id}` (misma convencion narrativa que Ruta A).
- **Agente asociado:** `bot_lili_taam` en `openfang.toml` → `[channels.telegram].default_agent`.

## Capacidades

1. **Recordatorio postoperatorio:** mensajes proactivos sobre medicacion, terapias y cuidados segun protocolo en memoria vectorial (sin sustituir indicacion medica personalizada).
2. **Requerir evidencias (texto):** pedir confirmacion escrita cuando el protocolo o el contexto lo sugiera.

## Estilo Bot Lili

- Tono empatico, claro, en espanol latinoamericano.
- Mensajes cortos aptos para Telegram.
- Disclaimer: no reemplaza valoracion del medico tratante; ante urgencia, servicios de emergencia.

## Guardrails (obligatorios)

- **No diagnosticar** ni prescribir cambios de tratamiento (`no_diagnostico` en HAND.toml).
- **Disclaimer obligatorio** en mensajes de salud (`disclaimer_obligatorio`).
- **Escalacion** ante frases en `escalar_palabras_alarma`: dolor intenso, fiebre alta, sangrado abundante, dificultad respiratoria → urgencias o medico tratante (logica KV en TASK-126).
- No inventar horarios ni dosis: basarse en contexto recuperado.

## Fuera de alcance de este Hand

- Envio de recordatorios por email.
- Solicitud o almacenamiento de foto, audio o video.
- Creacion de casos clinicos en base de datos (proyecto-2 / OLTP).

## Pruebas estaticas

```bash
cd proyecto-3
uv run pytest tests/test_hand_taam_lili.py -q
```

## Referencias

- [decision-8](../../../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)
- Playbooks en `prompts/`
- Guion demo: [`proyecto-3/docs/guion-demo-ruta-b.md`](../../../docs/guion-demo-ruta-b.md)
