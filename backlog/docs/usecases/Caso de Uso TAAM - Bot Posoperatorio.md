# Bot de la FVL para el seguimiento postoperatorio (TAAM)

> **Arquitectura M3 (MVP):** Ruta A + Telegram vía 2 en `proyecto-2/`. ADR vigente: [decision-7 — Arquitectura M3 TAAM](../../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md). Milestone: [m-0 — Agentic Final Project](../../milestones/m-0%20-%20agentic-final-project.md).
>
> **Separación M2:** el asistente institucional del Módulo 2 permanece en `proyecto-1/` (LangGraph, `POST /api/agente/stream`, SSE). Este documento describe solo el MVP **TAAM** (Técnicas Avanzadas — seguimiento postoperatorio).

---

## 1. Resumen ejecutivo

### Problema

La Fundación Valle del Lili (FVL) necesita acompañar a pacientes en el **postoperatorio** (medicación, cuidados, señales de alarma) sin depender únicamente de visitas presenciales. El personal clínico requiere visibilidad de las interacciones y de los casos que requieren revisión humana.

### Solución MVP

- **Bot Lili** atiende al paciente por **Telegram** (canal de demostración del curso).
- **Integración vía 2:** webhook y envío de mensajes en el mismo **FastAPI** de `proyecto-2/` (sin N8N ni WhatsApp).
- **Ruta A (M3):** agente LangChain con `create_agent`, tools con esquemas Pydantic, RAG sobre PDFs de protocolo en **Qdrant** dedicado, memoria en **PostgreSQL** TAAM.
- **Panel web** en `proyecto-2/frontend/` (misma línea visual que M2) para administración de catálogo, alta de casos, emparejamiento y seguimiento de alertas.

### Alcance funcional resumido

| Incluido (5 UC-MVP) | Diferido (Fase 2 / Fuera de MVP) |
| --- | --- |
| Catálogo procedimiento + PDF | Gestión completa de usuarios/RBAC |
| Alta caso + código Telegram | Recordatorios por email de citas |
| Chat Bot + triage + HITL urgente | Evidencias multimedia en Telegram |
| Recordatorios por plantilla + fecha cirugía | Intervención del cirujano en el hilo |
| Panel lectura + marcar alerta revisada | Extracción perfecta de horarios desde PDF |

---

## 2. Glosario

| Término | Definición |
| --- | --- |
| **TAAM** | Producto M3 de seguimiento postoperatorio en `proyecto-2/`. |
| **Bot Lili** | Subsistema conversacional (Telegram + agente); **no** es un actor humano numerado. |
| **Protocolo general** | Recomendaciones del **tipo de procedimiento** (PDF indexado en Qdrant, colección `taam_protocolos`). |
| **Protocolo / notas de caso** | Datos específicos del paciente (`notas_especificas`, metadatos del caso); **sin** PDF obligatorio por paciente en MVP. |
| **Triage** | Clasificación automática de la consulta en severidad cerrada: `info`, `seguimiento`, `urgente`. |
| **`session_id`** | Identificador del hilo LangChain: `telegram:{chat_id}` (`chat_id` entero de Telegram). |
| **Emparejamiento** | Vinculo OLTP entre `caso_postoperatorio_id` y `telegram_chat_id` mediante código de un solo uso (TTL). |
| **Red flag** | Condición clínica o texto que fuerza severidad `urgente` y flujo HITL. |
| **HITL** | Human-in-the-loop: `HumanInTheLoopMiddleware` pausa o marca revisión humana en severidad `urgente`. |
| **Ruta A / vía 2** | Function calling estricto + FastAPI propio para Telegram (ver decision-7). |

---

## 3. Actores

| Actor | Descripción | UC-MVP donde participa |
| --- | --- | --- |
| **Paciente** | Usuario final en Telegram; no accede al panel web en MVP. | 03, 04 (receptor) |
| **Asistente quirúrgico** | Registra casos postoperatorio y entrega código de emparejamiento. | 02 |
| **Personal clínico** | Rol unificado (cirujano y/o asistente) que revisa conversaciones y alertas; **solo lectura** + marcar revisado en MVP. | 05 |
| **Administrador de catálogo** | Gestiona tipos de procedimiento y PDF de protocolo general. | 01 |
| **Bot Lili** | Subsistema: webhook → `POST /chat` → agente → respuesta Telegram. | 03, 04 |

> En el documento legacy, «Cirujano» y «Asistente» aparecían separados en la misma fila de seguimiento; en MVP se unifican en **Personal clínico** para UC-MVP-05.

---

## 4. Modelo de triage (transversal a UC-MVP-03)

| Severidad | Criterio orientativo | Acción del bot | HITL | Persistencia |
| --- | --- | --- | --- | --- |
| **`info`** | Dudas generales, FAQs, sin síntomas alarmantes. | Responde con RAG/FAQ; disclaimer médico. | No | Opcional log en historial |
| **`seguimiento`** | Síntoma leve o duda que requiere vigilancia; no emergencia inmediata. | Responde + sugiere contacto con equipo; tool `escalar_a_equipo` con severidad `seguimiento`. | No | Fila en `alertas_triage` (`revisado=false` por defecto) |
| **`urgente`** | Red flags (dolor intenso, sangrado abundante, fiebre alta, dificultad respiratoria, etc.). | Mensaje corto al paciente: acudir a urgencias / contactar equipo; **no** sustituye emergencias. | **Sí** (`HumanInTheLoopMiddleware`) | `alertas_triage` + flag `requiere_revision_humana` en respuesta `/chat` |

**Regla de negocio (disclaimer):** todas las respuestas al paciente deben indicar que el bot **no reemplaza** al médico tratante y que ante urgencia debe acudir a servicios de emergencia.

**Tool:** `clasificar_triage` (output Pydantic: `severidad`, `rationale`). **Tool:** `escalar_a_equipo` inserta en `alertas_triage`.

---

## 5. Casos de uso MVP

### UC-MVP-01 — Registrar tipo de procedimiento y protocolo PDF

| Campo | Detalle |
| --- | --- |
| **ID** | UC-MVP-01 |
| **Actor principal** | Administrador de catálogo |
| **Objetivo** | Registrar un tipo de procedimiento postoperatorio con su documento PDF de recomendaciones generales, habilitando ingesta RAG y plantillas de recordatorio. |
| **Precondiciones** | Staff autenticado con rol admin (`X-Admin-Key` o JWT según TASK-105). Backend TAAM y almacenamiento `data/taam/` disponibles. |
| **Postcondiciones** | Existe `tipos_procedimiento` con `hash_sha256` del PDF; archivo en `data/taam/procedimientos/{id}/protocolo.pdf`; estado de indexación listo para TASK-101. |

**Flujo principal**

1. El administrador abre el panel **Catálogo de procedimientos** (`features/admin-procedimientos/`).
2. Completa nombre, código interno y selecciona archivo PDF (validación tamaño/MIME en cliente y servidor).
3. El sistema envía `POST /api/admin/procedimientos` (multipart: metadata + PDF).
4. El backend persiste la fila y guarda el PDF; responde `id` y estado `indexacion_estado=pendiente`.
5. Se ejecuta ingesta (script `ingestar_protocolo_pdf.py` o job asíncrono): chunks en Qdrant colección `taam_protocolos`.
6. El listado muestra `indexacion_estado=ok` y versión vector; el procedimiento queda disponible para UC-MVP-02.

**Flujos alternativos / excepciones**

- **A1 — PDF inválido:** respuesta 422; el usuario corrige el archivo sin crear fila huérfana.
- **A2 — Reemplazo de PDF:** `PATCH /api/admin/procedimientos/{id}` incrementa versión/hash y dispara reindexación.
- **A3 — Falla de ingesta:** estado `error`; UC-MVP-02 no permite seleccionar ese tipo hasta `ok`.

**Reglas de negocio**

- Tamaño máximo sugerido: 10 MB; solo `application/pdf`.
- No exponer rutas absolutas del servidor en JSON.
- El PDF es **protocolo general**, no historial clínico del paciente.

**Datos persistidos**

- Tabla `tipos_procedimiento` (nombre, código, hash, versión vector, rutas lógicas).
- Vectores en Qdrant con payload `tipo_procedimiento_id`, página, nombre archivo.

**Criterios de aceptación (demo)**

- [ ] Se lista al menos un procedimiento con estado de indexación visible.
- [ ] Un PDF de prueba queda indexado (`ok`) antes de registrar casos.

---

### UC-MVP-02 — Vincular paciente a seguimiento postoperatorio

| Campo | Detalle |
| --- | --- |
| **ID** | UC-MVP-02 |
| **Actor principal** | Asistente quirúrgico |
| **Objetivo** | Registrar el caso quirúrgico de un paciente y generar un código de emparejamiento para Telegram **sin** subir PDF por paciente. |
| **Precondiciones** | Existe al menos un `tipo_procedimiento` con `indexacion_estado=ok`. Asistente autenticado en panel staff. |
| **Postcondiciones** | Caso `activo` en `casos_postoperatorio`; código de emparejamiento con TTL; tras UC-MVP-03, fila en `vinculos_telegram`. |

**Flujo principal**

1. El asistente abre **Nuevo caso** (`features/casos/`).
2. Selecciona tipo de procedimiento (solo indexados `ok`), ingresa `paciente_doc_id`, `paciente_nombre`, `cirujano_id`, `cirujano_nombre`, `fecha_cirugia` (ISO) y `notas_especificas` opcionales.
3. `POST /api/staff/casos` crea el caso y devuelve `id`.
4. El asistente pulsa **Generar código** → `POST /api/staff/casos/{id}/codigo-emparejamiento` (6–8 caracteres, TTL 24 h).
5. La UI muestra el código, botón copiar y texto: «En Telegram envíe `/start CODIGO` al bot» (deep link `t.me/{bot}?start=CODIGO` si está configurado).
6. El paciente envía `/start CODIGO` en Telegram.
7. Webhook invoca `POST /api/telegram/emparejar` → crea `vinculos_telegram`; el bot confirma en español.
8. El listado de casos muestra indicador **Vinculado Telegram: sí**.

**Flujos alternativos / excepciones**

- **E1 — Código expirado o inválido:** mensaje amable en Telegram; no se activa chat clínico.
- **E2 — `chat_id` ya vinculado a otro caso activo:** 409; asistente debe cerrar o desvincular según política futura.
- **E3 — Procedimiento sin indexar:** 422 al crear caso o al generar código.
- **E4 — Regenerar código:** invalida el anterior; nuevo TTL.

**Reglas de negocio**

- Un `telegram_chat_id` solo a un caso **activo** a la vez.
- Código de un solo uso (invalidar tras emparejamiento exitoso).
- **No** se exige PDF por paciente en MVP.

**Datos persistidos**

- `casos_postoperatorio`, `codigos_emparejamiento`, `vinculos_telegram`.

**Criterios de aceptación (demo)**

- [ ] Caso creado con datos ficticios (ver sección 10).
- [ ] Emparejamiento exitoso desde teléfono de prueba antes del chat clínico.

---

### UC-MVP-03 — Consultar Bot Lili por Telegram (núcleo de demo)

| Campo | Detalle |
| --- | --- |
| **ID** | UC-MVP-03 |
| **Actor principal** | Paciente (vía Bot Lili) |
| **Objetivo** | Obtener orientación postoperatoria contextualizada (RAG + FAQs), con triage y escalación cuando corresponda. |
| **Precondiciones** | Caso activo con `vinculos_telegram` válido. Agente TASK-103 desplegado. Webhook Telegram configurado. |
| **Postcondiciones** | Mensajes en checkpointer (`session_id=telegram:{chat_id}`); alertas en `alertas_triage` si aplica; respuesta enviada por Telegram. |

**Flujo principal**

1. El paciente escribe un mensaje de texto en Telegram (p. ej. «¿puedo tomar ibuprofeno hoy?»).
2. `POST /api/telegram/webhook` (alias documentado: `/api/integracion/telegram/webhook`) valida secret y parsea el `Update`.
3. El integrador construye `session_id=telegram:{chat_id}` y llama internamente a `POST /chat` con el texto.
4. El agente ejecuta `obtener_contexto_caso` y, según la consulta, `consultar_protocolo_rag` y/o `faq_postoperatorio`.
5. `clasificar_triage` devuelve severidad; si `urgente`, `HumanInTheLoopMiddleware` y `escalar_a_equipo`.
6. `dynamic_prompt` compone respuesta con disclaimer y nombre del paciente si está disponible.
7. La API devuelve JSON (`respuesta`, `severidad_triage`, `requiere_revision_humana`, `fuentes`).
8. El cliente Telegram envía `sendMessage` al paciente (texto truncado si > 4096 caracteres).

**Flujos alternativos / excepciones**

- **E1 — Sin emparejamiento:** `/chat` responde 403; Telegram muestra mensaje instructivo (sin contenido clínico).
- **E2 — RAG vacío:** mensaje cortés + escalación o «consulte a su equipo».
- **E3 — Red flag explícita:** forzar `urgente` aunque el clasificador dude.
- **E4 — Tool falla:** texto fijo de cortesía definido en prompt del agente.

**Reglas de negocio**

- No diagnosticar ni prescribir; orientar según protocolo indexado y FAQs.
- Disclaimer médico en cada interacción relevante.
- Severidades cerradas: `info`, `seguimiento`, `urgente` (ver sección 4).

**Datos persistidos**

- Historial LangChain (`PostgresSaver`), `alertas_triage`, opcional espejo para panel.

**Criterios de aceptación (demo)**

- [ ] Pregunta de FAQ responde con severidad `info`.
- [ ] Pregunta con síntoma alarmante genera alerta `urgente` visible en UC-MVP-05.
- [ ] Chat sin vínculo no entrega consejo clínico.

---

### UC-MVP-04 — Recordatorios proactivos por Telegram

| Campo | Detalle |
| --- | --- |
| **ID** | UC-MVP-04 |
| **Actor principal** | Bot Lili (scheduler) / Asistente (disparo manual demo) |
| **Objetivo** | Enviar recordatorios de cuidados postoperatorios según **plantilla** del tipo de procedimiento y **fecha de cirugía**, sin email ni agenda hospitalaria. |
| **Precondiciones** | Plantillas `plantillas_recordatorio` asociadas al `tipo_procedimiento_id`. Caso con vínculo Telegram. |
| **Postcondiciones** | Registro en `recordatorios_enviados` con `enviado_at`; mensaje recibido en Telegram. |

**Flujo principal**

1. Al crear el caso (UC-MVP-02), el sistema calcula `programado_at = fecha_cirugia + offset_horas` por cada plantilla activa.
2. Un job periódico (APScheduler / asyncio) busca recordatorios pendientes (`programado_at <= now()`, `enviado_at IS NULL`).
3. Para cada uno, resuelve `telegram_chat_id` del caso; si no hay vínculo, omite y registra log.
4. Renderiza plantilla con `{nombre_paciente}`, `{tipo_procedimiento}`, `{texto_cuidado}`.
5. Envía mensaje vía Bot API (misma integración TASK-106) y marca `enviado_at`.

**Flujos alternativos / excepciones**

- **A1 — Demo en vivo:** `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` envía el siguiente recordatorio sin esperar el scheduler.
- **E1 — Sin vínculo Telegram:** no enviar; no duplicar en reintento (transacción por `recordatorio_id`).

**Reglas de negocio**

- **No** recordatorios por email en MVP.
- No depender de extracción OCR perfecta de horarios del PDF; offsets estructurados + plantilla.
- Mitigación decision-7: cronograma no es única fuente RAG.

**Datos persistidos**

- `plantillas_recordatorio`, `recordatorios_programados`, `recordatorios_enviados`.

**Criterios de aceptación (demo)**

- [ ] Al menos un recordatorio recibido en Telegram (manual o job con fecha artificial).
- [ ] Verificado que no se usa canal email.

---

### UC-MVP-05 — Revisar conversaciones y alertas (solo lectura)

| Campo | Detalle |
| --- | --- |
| **ID** | UC-MVP-05 |
| **Actor principal** | Personal clínico |
| **Objetivo** | Visualizar el hilo paciente–bot, la bandeja de alertas de triage y marcar alertas como revisadas (doble check). |
| **Precondiciones** | Autenticación staff (JWT/API key TASK-105). Existen mensajes y/o alertas del caso demo. |
| **Postcondiciones** | Alerta con `revisado=true`, timestamp y opcional `staff_id`; auditoría de quién revisó. |

**Flujo principal**

1. El clínico inicia sesión en el panel TAAM (`features/seguimiento/`).
2. Abre **Bandeja de alertas** → `GET /api/staff/alertas?revisado=false` (filtros severidad, paginación).
3. Las tarjetas muestran color semántico: info / seguimiento / urgente (urgente arriba).
4. Abre detalle de caso → `GET /api/staff/casos/{id}/conversacion` (mensajes del thread `telegram:{chat_id}`).
5. Consulta `GET /api/staff/casos/{id}/resumen` (último triage, conteo mensajes, próximo recordatorio).
6. Tras validar, `PATCH /api/staff/alertas/{id}` con `{ "revisado": true }`.
7. La alerta desaparece del filtro «pendientes»; opcional notificación toast (polling 30 s).

**Flujos alternativos / excepciones**

- **E1 — Sin alertas pendientes:** bandeja vacía con mensaje explicativo.
- **A1 — Política de privacidad:** `telegram_chat_id` enmascarado (últimos 4 dígitos) para rol asistente.

**Reglas de negocio**

- **Sin** edición de mensajes ni respuesta del cirujano dentro de Telegram en MVP (tooltip en UI).
- Usar **datos ficticios** en capturas (sin PHI real).

**Datos persistidos**

- Lectura desde `PostgresSaver` / tabla espejo; actualización `alertas_triage`.

**Criterios de aceptación (demo)**

- [ ] Alerta generada en UC-MVP-03 aparece en bandeja.
- [ ] Marcar revisado es idempotente y persiste.

---

## 6. Fuera de MVP (explícito)

Capacidades del **documento original** (tabla de 8 filas) y del ADR que **no** están en los 5 UC-MVP:

| # | Capacidad original | Motivo de exclusión MVP |
| --- | --- | --- |
| 1 | **Gestionar usuarios** (RBAC completo de actores) | Solo auth staff mínima (TASK-105); sin CRUD de roles. |
| 2 | **Recordatorios de citas por email** | Canal MVP = Telegram; sin integración de agenda hospitalaria. |
| 3 | **Requerir evidencias** (foto, audio, video) | Complejidad de almacenamiento y moderación; Fase 2. |
| 4 | **Intervenir en el chat** (cirujano responde en Telegram) | Panel solo lectura; sin API de envío staff al hilo. |
| 5 | **Registrar procedimiento por paciente con PDF** | Sustituido por protocolo general + notas de caso (UC-MVP-02). |
| 6 | **Extracción automática fiel de horarios/dosis desde PDF** | Riesgo aceptado; recordatorios por plantilla + fecha (decision-7). |
| 7 | **WhatsApp / N8N / OpenFang (Ruta B)** | Curso exige vía 2 en FastAPI. |
| 8 | **Doble rol cirujano vs asistente en seguimiento** | Unificado en Personal clínico para UC-MVP-05. |

---

## 7. Fase 2 (tabla de evolución)

| Capacidad | Dependencias típicas | UC / nota |
| --- | --- | --- |
| Evidencias multimedia en Telegram | Almacenamiento S3, antivirus, UI moderación | Nuevo UC-F2-01 |
| Citas y recordatorios email | Integración agenda, SMTP | Extiende UC legacy «Recordatorios de Citas» |
| RBAC granular (cirujano vs asistente vs admin) | TASK-105 ampliado | Políticas por endpoint |
| Intervención en vivo en conversación | API envío staff → Telegram | Ex «Consultar e intervenir» |
| Gestión de usuarios institucionales | IdP, tablas rol-permiso | Ex «Gestionar usuarios» |
| Analytics y exportación de conversaciones | BI, anonimización | Panel ampliado |

---

## 8. Matriz de trazabilidad (UC → API → tool → frontend → tarea)

| UC | Endpoints FastAPI (previstos) | Tools LangChain (`name`) | Frontend `proyecto-2/` | Tarea Backlog |
| --- | --- | --- | --- | --- |
| **UC-MVP-01** | `POST/GET/PATCH /api/admin/procedimientos` | — (ingesta: script, no tool runtime) | `features/admin-procedimientos/` | TASK-100, TASK-101, TASK-111 |
| **UC-MVP-02** | `POST/GET /api/staff/casos`, `POST .../codigo-emparejamiento`, `POST /api/telegram/emparejar` | `obtener_contexto_caso` | `features/casos/` | TASK-102, TASK-112 |
| **UC-MVP-03** | `POST /chat`, `POST /api/telegram/webhook` | `consultar_protocolo_rag`, `faq_postoperatorio`, `clasificar_triage`, `escalar_a_equipo`, `obtener_contexto_caso` | — (Telegram) | TASK-103, TASK-104, TASK-106 |
| **UC-MVP-04** | Job interno + `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` | — (scheduler; opcional tool futura) | Indicador en detalle de caso | TASK-107 |
| **UC-MVP-05** | `GET /api/staff/casos/{id}/conversacion`, `GET /api/staff/alertas`, `PATCH /api/staff/alertas/{id}`, `GET .../resumen` | Lectura de historial generado por UC-03 | `features/seguimiento/` | TASK-108, TASK-113 |

**Infra transversal:** TASK-98 (scaffold), TASK-99 (esquema Postgres), TASK-105 (auth), TASK-109–110 (frontend base), TASK-114 (semilla demo), TASK-115 (tests).

---

## 9. Guion de sustentación (15 minutos)

**Roles:** Presentador (laptop + panel), Paciente (teléfono con Telegram), opcional Asistente (segundo dispositivo).

**Pre-requisitos:** `docker compose` TAAM arriba (~8001), `sembrar_demo_taam.py` ejecutado o datos de sección 10; webhook/ngrok configurado; bot Telegram de prueba.

| Min | Paso | Qué mostrar | Evidencia esperada |
| --- | --- | --- | --- |
| 0–1 | Intro | decision-7, diagrama contexto: Telegram → FastAPI → agente → PG/Qdrant; **no** abrir UI M2 | Separación proyecto-1 vs proyecto-2 |
| 1–3 | UC-MVP-01 | Panel admin: listar procedimiento demo «Colecistectomía laparoscópica» con indexación `ok` | GET procedimientos |
| 3–5 | UC-MVP-02 | Crear caso **Paciente Demo A** o mostrar caso sembrado; generar/copiar código; paciente envía `/start CODIGO` | Vínculo «sí» en listado |
| 5–9 | UC-MVP-03 | Paciente pregunta FAQ («¿cuándo puedo caminar?») → respuesta `info`; luego mensaje red flag («sangrado abundante») → respuesta urgente + disclaimer | Logs `POST /chat`; severidad en JSON |
| 9–11 | UC-MVP-04 | Disparar recordatorio de prueba o mostrar mensaje programado en Telegram | Mensaje plantilla en teléfono |
| 11–14 | UC-MVP-05 | Panel: bandeja alerta `urgente`; abrir conversación; **Marcar revisado** | PATCH alerta; filtro pendientes vacío |
| 14–15 | Cierre | Matriz UC, riesgos PDF/plantillas, roadmap Fase 2 | — |

**Frases clave para el profesor:** «Ruta A con tools tipadas», «HITL en urgente», «M2 institucional intacto en proyecto-1».

---

## 10. Datos de prueba (ficticios, sin PHI real)

### Procedimiento y PDF

| Campo | Valor demo |
| --- | --- |
| `tipo_procedimiento` | `COLE-LAP-001` — Colecistectomía laparoscópica (ficticio) |
| PDF | `data/taam/demo/colecistectomia-protocolo-sintetico.pdf` (texto generado para curso) |
| Estado indexación | `ok` tras `ingestar_protocolo_pdf.py` |

### Pacientes / casos

| Caso | `paciente_doc_id` | Nombre | `fecha_cirugia` | Uso en demo |
| --- | --- | --- | --- | --- |
| A | `PAC-DEMO-001` | Ana Ficticia López | Hoy − 2 días | Emparejamiento + chat + alerta urgente |
| B | `PAC-DEMO-002` | Bruno Ficticio Ruiz | Hoy − 7 días | Segundo caso en listado; recordatorio |

### Staff (semilla)

| Rol | Identificador | Notas |
| --- | --- | --- |
| Admin catálogo | `admin@demo.taam` | Solo UC-MVP-01 |
| Asistente | `asistente@demo.taam` | UC-MVP-02 |
| Clínico | `clinico@demo.taam` | UC-MVP-05 |

### Telegram (laboratorio)

| Variable | Ejemplo (placeholder) |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | `123456789:AA...demo` (BotFather entorno curso) |
| `TELEGRAM_WEBHOOK_SECRET` | cadena aleatoria ≥ 32 chars |
| `VITE_TELEGRAM_BOT_USERNAME` | `FVL_Lili_Demo_Bot` |
| Chats de prueba | `telegram:111111111`, `telegram:222222222` (IDs ficticios en seed) |

### Preguntas sugeridas para UC-MVP-03

1. «¿Cuándo puedo retomar caminatas leves?» → severidad esperada: `info`.
2. «Tengo sangrado abundante en la herida» → severidad esperada: `urgente` + alerta en panel.

---

## 11. Referencias

- [decision-7 — Arquitectura M3 TAAM](../../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md)
- [decision-3 — Agente M2 (proyecto-1)](../../decisions/decision-3%20-%20Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md)
- [m-0 — Agentic Final Project](../../milestones/m-0%20-%20agentic-final-project.md)
- Tarea documentación: TASK-97 · ADR: TASK-96 · Semilla y guion extendido: TASK-114

---

## Anexo — Mapeo documento legacy → MVP

| Fila legacy | Destino MVP |
| --- | --- |
| Registrar procedimiento (admin) | UC-MVP-01 |
| Registrar procedimiento quirúrgica (asistente) | UC-MVP-02 (sin PDF paciente) |
| Chat con Bot Lili | UC-MVP-03 |
| Recordatorio postoperatorio | UC-MVP-04 |
| Seguimiento interacciones / doble check triage | UC-MVP-05 |
| Gestionar usuarios | Fuera de MVP |
| Recordatorios citas email | Fuera de MVP |
| Requerir evidencias | Fuera de MVP |
| Consultar e intervenir chat | UC-MVP-05 (solo consulta) + Fase 2 intervención |
