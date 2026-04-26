---
name: backlog-decisions
description: Formato de registros de decision (YAML front matter) en backlog/decisions. Usar al crear, migrar o revisar ADR al estilo Backlog.md.
---

# Decisiones en `backlog/decisions/`

> Mantener el mismo contenido en `.cursor/skills/backlog-decisions/` y `.claude/skills/backlog-decisions/`.

## Cuando aplicar esta skill

- Crear un archivo nuevo en `backlog/decisions/`.
- Convertir un borrador sin front matter al formato canonico.
- Revisar que un PR cumpla el esquema esperado por [Backlog.md](https://github.com/MrLesk/Backlog.md).

Referencia de formato: [decision-1 en el repo upstream](https://github.com/MrLesk/Backlog.md/blob/main/backlog/decisions/decision-1%20-%20Use-Tailwind-CSS-v4-for-web-UI-development.md?plain=1).

## Checklist obligatorio

1. **Primeras lineas**: bloque YAML entre `---` y `---`.
2. **Campos**: `id`, `title`, `date` (ISO entre comillas simples), `status`.
3. **Despues del front matter**: linea en blanco + cuerpo Markdown.
4. **Nombre de archivo**: patron Backlog.md `decision-<N> - <Titulo-Slug>.md` (espacio-guion-espacio entre prefijo y slug); ASCII, Title-Case por palabra en el slug, sin tildes ni ene en el path; `id` debe ser `decision-<N>` del mismo `<N>` que en el nombre.

## Convencion de nombre de archivo

- Plantilla: `decision-1 - Use-Tailwind-CSS-v4-for-web-UI-development.md`
- Referencia: [archivo ejemplo en Backlog.md](https://github.com/MrLesk/Backlog.md/blob/main/backlog/decisions/decision-1%20-%20Use-Tailwind-CSS-v4-for-web-UI-development.md?plain=1).
- El numero `<N>` en el nombre y en `id` debe coincidir; al anadir una decision nueva, usar el siguiente entero libre en el directorio.

## Plantilla copiable

```markdown
---
id: decision-1
title: Titulo de la decision en una linea
date: '2026-04-26'
status: proposed
---

## Contexto

...

## Decision

...

## Consecuencias

### Positivas

- ...

### Negativas / riesgos

- ...

### Mitigacion

- ...

## Referencias

- ...
```

## Valores de `status`

Usar uno coherente en todo el directorio:

| Valor | Uso |
| --- | --- |
| `proposed` | En discusion o borrador. |
| `accepted` | Aprobada y vigente. |
| `rejected` | Descartada. |
| `deprecated` | Ya no aplica; indicar reemplazo en el cuerpo si existe. |
| `superseded` | Reemplazada por otra decision; enlazar `id` de la nueva en el cuerpo. |

## Regla vinculada

Ver **`.cursor/rules/backlog-decisions-format.mdc`** (se activa con archivos bajo `backlog/decisions/**`).
