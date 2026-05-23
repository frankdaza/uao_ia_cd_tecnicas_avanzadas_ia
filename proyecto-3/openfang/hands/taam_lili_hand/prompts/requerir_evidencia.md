# Playbook — Requerir evidencia en texto (Hand taam_lili_hand)

**Entrada HAND:** clave `[prompts].requerir_evidencia_texto` → este archivo.

## Objetivo

Cuando el seguimiento del protocolo lo indique, solicitar al paciente una **confirmacion escrita** (no multimedia en este MVP).

## Pasos sugeridos

1. Revisar si en el contexto del paciente aplica solicitud de evidencia (p. ej. confirmacion de toma de medicamento del dia).
2. Enviar mensaje claro indicando que se espera respuesta en texto.
3. Registrar la respuesta en memoria episodica de la sesion para consulta posterior en dashboard.
4. Flag futuro en Structured KV: `pendiente_evidencia` (implementacion TASK-125).

## Senales de alarma

Ante **dolor intenso**, **fiebre alta**, **sangrado abundante** o **dificultad respiratoria**, indicar urgencias antes de insistir en la evidencia.

## Plantilla (adaptar)

> Hola, para tu seguimiento postoperatorio necesito que me confirmes por este chat: [accion concreta, p. ej. si tomaste la dosis de la manana indicada]. Responde con un mensaje de texto. Si tienes dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, cuentamelo de inmediato y acude a urgencias si corresponde. Esta orientacion no reemplaza la valoracion de su medico tratante.

## Limites MVP

- No solicitar fotos, audios ni videos (Fase 2 / otro stack).
- No almacenar archivos adjuntos.
- Maximo un reintento si no hay respuesta en 24 h (TASK-125).
