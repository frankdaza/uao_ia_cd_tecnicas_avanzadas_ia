import { z } from 'zod'

/** Mismo contrato que el backend (``codigo_registro`` ASCII). */
export const CODIGO_REGISTRO_REGEX = /^[A-Za-z0-9._-]+$/

export const MedicoCuerpoSchema = z.object({
  codigo_registro: z
    .string()
    .min(1)
    .max(64)
    .regex(
      CODIGO_REGISTRO_REGEX,
      'Código de registro: solo letras, números, punto, guion y guion bajo.',
    ),
  nombre_completo: z.string().min(1).max(512),
  especialidad: z.string().max(256).optional(),
})

export type MedicoCuerpo = z.infer<typeof MedicoCuerpoSchema>

export const MedicoParcheSchema = z
  .object({
    codigo_registro: z
      .string()
      .min(1)
      .max(64)
      .regex(CODIGO_REGISTRO_REGEX, 'Código de registro: formato ASCII inválido.')
      .optional(),
    nombre_completo: z.string().min(1).max(512).optional(),
    especialidad: z.string().max(256).nullable().optional(),
  })
  .refine((v) => Object.keys(v).length > 0, {
    message: 'Debe enviar al menos un campo para actualizar.',
  })

export type MedicoParche = z.infer<typeof MedicoParcheSchema>
