---
name: cursor-ignore-files
description: Mantiene .cursorignore y .cursorindexingignore para secretos, indice del IDE y coherencia con Claude Code. Usar al cambiar exclusiones o revisar fuga de contexto.
---

# Archivos ignore de Cursor

> Mantener el mismo contenido en `.cursor/skills/cursor-ignore-files/` y `.claude/skills/cursor-ignore-files/`.

## Referencias

- [Ignore file (Cursor)](https://cursor.com/docs/reference/ignore-file)
- [Claude Code — sintaxis de permisos Read/Edit](https://code.claude.com/docs/en/permissions#permission-rule-syntax)
- Regla del proyecto: `.cursor/rules/cursor-ignore-files.mdc`

## Checklist al editar patrones

1. **Proposito**: `.cursorignore` bloquea agente, `@` y busqueda semantica; `.cursorindexingignore` solo el indice (menos agresivo).
2. **Secretos**: alinear [`.gitignore`](../../../.gitignore), [`.cursorignore`](../../../.cursorignore) y `permissions.deny` en [`.claude/settings.json`](../../../.claude/settings.json) (rutas `Read(/...)` relativas al repo en Claude Code).
3. **Corpus**: `data/markdown/` esta en **`.cursorindexingignore`** para reducir ruido del indice del IDE; el **runtime** del backend sigue leyendo archivos en disco. No excluir el corpus del indice si el equipo depende de buscarlo con `@` en Cursor sin abrir archivos.
4. **TAAM**: `data/taam/` (PDFs runtime) en `.cursorignore` y `.cursorindexingignore`; en `.gitignore` con `!**/.gitkeep`.
5. **Lockfile**: Cursor ignora `*.lock` por defecto en indexacion; mantener `!uv.lock` y `!proyecto-*/uv.lock` donde aplique.
6. **Probar**: `git check-ignore -v <ruta>` para sintaxis tipo gitignore.
7. **Limites**: la terminal y MCP **no** quedan bloqueados por `.cursorignore`; `permissions.deny` afecta herramientas de archivo de Claude, no `cat` en Bash salvo sandbox.
8. **Backlog**: nunca volcar claves reales en tareas o documentacion de `backlog/`.

## Claude Code

Usar `permissions.deny` con patrones `Read(/...)` (proyecto) documentados en la referencia oficial. No hay `.claudeignore` estandar en la raiz.
