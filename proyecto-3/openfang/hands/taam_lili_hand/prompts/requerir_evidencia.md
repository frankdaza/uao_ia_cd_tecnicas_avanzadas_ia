# Playbook — Requerir evidencia en texto (Hand taam_lili_hand)

**Entrada HAND:** clave `[prompts].requerir_evidencia_texto` → este archivo.

## Objetivo

Cuando el seguimiento del protocolo lo indique, solicitar al paciente una **confirmacion escrita** (no multimedia en este MVP).

## Pasos (orden sugerido)

1. Leer estado KV de la sesion `telegram:{chat_id}` (adaptador Python `src/hand/requerir_evidencia.py`; en runtime OpenFang puede mapearse a clave `evidencia:telegram:{chat_id}`).
2. Si `pendiente_evidencia` es `false`, no insistir salvo que el adaptador UC6 haya marcado pendiente tras recordatorio (`marcar_evidencia_tras_envio`).
3. Si `pendiente_evidencia` es `true` y aun no hay `ultimo_envio_iso`, enviar solicitud con plantilla (solo texto, disclaimer y senales de alarma).
4. Registrar envio en `ultimo_envio_iso` y auditoria `{OPENFANG_HOME}/audit/hand_evidencia.jsonl` (`tipo: hand_evidencia`, evento `solicitud_enviada`).
5. Al recibir respuesta del paciente en el chat reactivo, invocar `procesar_respuesta_evidencia`: texto valido → append en JSONL episodico y `pendiente_evidencia=false`; multimedia → ver seccion Negativo.

## Contrato KV (por sesion)

| Campo | Uso |
| --- | --- |
| `pendiente_evidencia` | Solicitud abierta |
| `ultimo_envio_iso` | Primera solicitud enviada |
| `ultimo_reintento_iso` | Reintento unico tras 24 h |
| `reintentos_evidencia` | Maximo `1` |
| `accion_solicitada` | Texto para la plantilla |
| `motivo_cierre` | `respuesta_recibida`, `cierre_sin_respuesta`, etc. |

Archivo local demo: `{OPENFANG_HOME}/kv/hand_evidencia/{chat_id}.json`.

## Disparo contextual (UC6 → UC7)

Tras un recordatorio postoperatorio enviado con exito, el adaptador UC6 puede llamar `iniciar_pendiente_evidencia` (flag `marcar_evidencia_tras_envio` en `ejecutar_recordatorio_postop`). **En pytest y CI** esa marca la hace Python, no el LLM del Hand.

## Negativo (multimedia)

Si el paciente envia foto, audio, video, sticker o mensaje que indique adjunto:

- Responder que el **MVP solo acepta texto** en el chat.
- **No** cerrar `pendiente_evidencia` como evidencia valida.
- Registrar evento `rechazo_multimedia` en auditoria.

Palabras indicio (no exhaustivo): foto, imagen, audio, video, voz, sticker, adjunto.

## Edge (24 h y reintento)

1. Tras `ultimo_envio_iso`, si pasan **24 h** sin respuesta valida y `reintentos_evidencia < 1`, enviar **un** reintento (misma plantilla adaptada) y actualizar `ultimo_reintento_iso`.
2. Tras el reintento, si pasan otras **24 h** sin respuesta valida, poner `pendiente_evidencia=false` y `motivo_cierre=cierre_sin_respuesta`.
3. No enviar mas de un reintento por solicitud.

## Senales de alarma

Ante **dolor intenso**, **fiebre alta**, **sangrado abundante** o **dificultad respiratoria**, indicar urgencias antes de insistir en la evidencia. El adaptador Python (`procesar_respuesta_evidencia`) marca KV `escalado=true` en `kv/hand_escalacion/`.

## Plantilla (adaptar)

> Hola, para su seguimiento postoperatorio necesito que me confirme por este chat: [accion concreta, p. ej. si tomaste la dosis de la manana indicada]. Responda con un mensaje de texto (en esta version no recibo fotos, audios ni videos). Si tiene dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, cuentemelo de inmediato y acuda a urgencias si corresponde. Esta orientacion no reemplaza la valoracion de su medico tratante.

## Limites MVP

- No solicitar ni almacenar fotos, audios ni videos (Fase 2 / otro stack).
- Maximo un reintento si no hay respuesta en 24 h (ver Edge).

## Auditoria (Ruta B)

Tras cada tick o disparo manual del adaptador Python, lineas en `{OPENFANG_HOME}/audit/hand_evidencia.jsonl` con `tipo: hand_evidencia` y eventos `solicitud_enviada`, `reintento_enviado`, `cierre_sin_respuesta`, `respuesta_texto_registrada`, `rechazo_multimedia`.
