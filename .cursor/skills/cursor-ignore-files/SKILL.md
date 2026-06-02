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
5. **proyecto-3 Ruta B**: `proyecto-3/openfang/data/` (runtime OpenFang, JSONL/SQLite) en ambos ignores de Cursor + `Read(/proyecto-3/openfang/data/**)` en Claude; `proyecto-3/analisis_tsne/output/` (artefactos t-SNE) en ambos ignores. No ignorar `openfang/hands/` ni scripts de install.
6. **`.env.example`**: `!**/.env.example` en `.cursorignore` para no bloquear plantillas (task-118).
7. **Lockfile**: Cursor ignora `*.lock` por defecto en indexacion; mantener `!uv.lock` y `!proyecto-*/uv.lock` donde aplique.
8. **Probar**: `git check-ignore -v <ruta>` para sintaxis tipo gitignore.
9. **Limites**: la terminal y MCP **no** quedan bloqueados por `.cursorignore`; `permissions.deny` afecta herramientas de archivo de Claude, no `cat` en Bash salvo sandbox.
10. **Backlog**: nunca volcar claves reales en tareas o documentacion de `backlog/`.

## Claude Code

Usar `permissions.deny` con patrones `Read(/...)` (proyecto) documentados en la referencia oficial. No hay `.claudeignore` estandar en la raiz.
