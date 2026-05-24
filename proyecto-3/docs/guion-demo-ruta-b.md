# Guion demo en vivo — Ruta B (15 minutos)

Sustentacion **100 % practica** (sin diapositivas): codigo, terminal, dashboard OpenFang y Telegram en vivo.

| Documento | Uso |
| --- | --- |
| [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) | ADR Ruta B |
| [doc-008](../../backlog/docs/doc-008%20-%20Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md) | Arquitectura operativa y comparativa A vs B |
| [dashboard-openfang.md](dashboard-openfang.md) | UC4, JSONL, auditoria Hand |
| [telegram-bot-setup.md](telegram-bot-setup.md) | BotFather, token, comandos |

**Roles:** presentador (laptop), paciente (Telegram en telefono). Bot **distinto** al de `proyecto-2/`.

---

## Checklist pre-demo (15–30 min antes)

| Item | Comando / verificacion | OK |
| --- | --- | --- |
| Directorio | `cd proyecto-3` | |
| OpenFang 0.6.9 | `./scripts/instalar_openfang.sh --verificar-only` y `openfang --version` | |
| PATH | `export PATH="$HOME/.openfang/bin:$PATH"` si hace falta | |
| Entorno | `cp .env.example .env` (una vez); editar `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN` | |
| Dependencias Python | `uv sync` | |
| Arranque E2E | `./scripts/arrancar_dev.sh` (o `--sin-telegram` sin ping getMe) | |
| Health OS | `curl -sS http://127.0.0.1:4200/api/health` | |
| Dashboard | Abrir `http://127.0.0.1:4200` | |
| Hand activo | Log de `arrancar_dev` o `openfang hand list` → `taam_lili_hand` | |
| Pregunta RAG | Frase preparada sobre protocolo FVL / postoperatorio | |

**Tests vs demo en vivo:** `uv run pytest -q` usa mocks (TASK-132); la sustentacion con ingesta/RAG/Telegram real requiere claves en `.env`. No pegar tokens en este documento.

---

## Tabla minuto a minuto (15 min)

| Min | Paso | Pantalla / terminal | Comandos exactos | Evidencia |
| --- | --- | --- | --- | --- |
| 0–2 | Contexto A vs B | Arbol `proyecto-3/` vs `proyecto-2/`; abrir decision-8 y doc-008 §2 | (navegador / IDE) | Separacion M2 (`proyecto-1`), Ruta A, Ruta B |
| 3–5 | Memoria 6 capas + dashboard | `http://127.0.0.1:4200`; [dashboard-openfang.md](dashboard-openfang.md) | Tras arranque: `openfang sessions --json` (opcional) | Sesiones, memoria semantica |
| 6–8 | Ingesta / RAG | Log de ingesta (ya en `arrancar_dev`) o terminal aparte | `uv run python ingesta/indexar_corpus_openfang.py --solo-markdown --limite 20` (opcional repaso) | Respuesta coherente sobre corpus FVL en chat |
| 9–11 | Hand + Telegram en vivo | Telefono → bot Ruta B; terminal audit | Ver bloque «Comandos de referencia» abajo | Mensaje paciente + opcional proactivo Hand ~30 s |
| 12–15 | t-SNE + cierre | Notebook o PNG exportado | `uv run jupyter notebook analisis_tsne/notebooks/analisis_tsne.ipynb` (o VS Code) | 2–3 clusters + tabla verbal A vs B |

**Frases clave:** «OpenFang puro sin OLTP», «Hand procedural cada 30 s en demo», «Ruta A tiene panel y alertas en Postgres».

---

## Narrativa por bloques (detalle)

### Minuto 0–2 — Contexto arquitectonico

- Mostrar arbol `proyecto-3/` vs `proyecto-2/` (Ruta A vs Ruta B en paralelo).
- Abrir [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) y explicar alcance **OpenFang puro** (sin OLTP ni panel React).

### Minuto 3–5 — Memoria e ingesta

- Dashboard OpenFang: memoria, sesiones, JSONL ([dashboard-openfang.md](dashboard-openfang.md)).
- Una frase: corpus desde `data/markdown/` y PDFs `data/taam/`.

### Minuto 6–8 — Hand autonomo (config)

- Mostrar `openfang/hands/taam_lili_hand/HAND.toml` y `SKILL.md` (guardrails: no diagnostico).
- Schedule demo: `every_secs = 30` (recordatorio + evidencia texto).

### Minuto 9–11 — Prueba de fuego Telegram

- Profesor o publico envia mensaje al **bot Ruta B**.
- Narrar: Update → bridge OpenFang → RAG memoria → OpenAI → respuesta.
- Pregunta sugerida: cuidado postoperatorio o medicacion segun protocolo ingerido.

### Minuto 12–15 — t-SNE y cierre

- Abrir notebook o grafico exportado; interpretar clusters (alarma, medicacion, agradecimiento).
- Cierre: Ruta A tiene OLTP + panel; Ruta B demuestra Agent OS + Hands. Limites: sin emparejamiento clinico ni evidencias multimedia.

---

## Comandos de referencia (copiar/pegar)

```bash
cd proyecto-3
export PATH="$HOME/.openfang/bin:$PATH"
cp .env.example .env   # si aun no existe
uv sync
./scripts/arrancar_dev.sh
# Solo verificacion bot (sin arranque completo):
./scripts/verificar_telegram_bot.sh
```

**Hand / UC6–UC7 (demo manual):**

```bash
uv run python scripts/disparar_recordatorio_hand.py --solo-simular
uv run python scripts/disparar_recordatorio_hand.py --marcar-evidencia
uv run python scripts/disparar_evidencia_hand.py --marcar-pendiente CHAT_ID --solo-simular
```

**Historial UC4:**

```bash
uv run python scripts/consultar_historial_sesion.py --session-id telegram:900001
```

**Auditoria Hand:**

```bash
tail -n 3 openfang/data/audit/hand_recordatorio.jsonl
tail -n 3 openfang/data/audit/hand_evidencia.jsonl
```

Sustituir `CHAT_ID` por el entero del chat de prueba (ficticio `900001` en docs; no usar IDs reales de pacientes en slides).

---

## Preguntas frecuentes del jurado

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Por que dos proyectos TAAM? | Ruta A evaluable con LangChain; Ruta B demuestra OpenFang sin romper decision-7. |
| ¿Donde esta el triage clinico? | En `proyecto-2/` (alertas Postgres); Ruta B solo memoria del OS y dashboard. |
| ¿Soberania de datos? | Documentar fallback Ollama; MVP acordado usa OpenAI como en proyecto-2. |

## Rollback si falla Telegram

1. Mostrar respuesta en dashboard OpenFang (mismo agente).
2. Mostrar ultimo JSONL de sesion en `OPENFANG_HOME` (ver [dashboard-openfang.md](dashboard-openfang.md)).
3. Explicar pin de version OpenFang y token del bot dedicado Ruta B.
