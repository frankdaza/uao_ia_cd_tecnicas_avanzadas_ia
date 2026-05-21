---
id: TASK-112
title: >-
  Frontend TAAM: registro casos postoperatorio y código emparejamiento
  (UC-MVP-02)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
labels:
  - modulo-3
  - taam
  - frontend
  - asistente
milestone: m-0
dependencies:
  - TASK-102
  - TASK-110
priority: high
ordinal: 2160
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El asistente da de alta casos y entrega código al paciente para Telegram.

## Objetivo

Feature `features/casos/`.

## Pantallas

- Formulario nuevo caso: select tipo procedimiento (solo indexados ok), datos paciente, cirujano, fecha cirugía, notas.
- Tras crear: modal con **código de emparejamiento** grande + instrucción «envíe /start CODIGO al bot» + TTL.
- Listado casos activos con indicador «vinculado Telegram» sí/no.
- Botón regenerar código (invalida anterior).

## UX crítica para demo

- Copiar código al portapapeles.
- Mostrar deep link `t.me/BotName?start=CODIGO` si hay variable `VITE_TELEGRAM_BOT_USERNAME`.

## Fallas a evitar

- Permitir elegir procedimiento sin indexación RAG.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Crear caso muestra código y expiración
- [ ] #2 Listado distingue vinculado vs pendiente
- [ ] #3 Select procedimiento solo muestra tipos indexados
- [ ] #4 Regenerar código invalida el anterior (verificado en API)
- [ ] #5 Textos e instrucciones en español latinoamericano
<!-- AC:END -->
