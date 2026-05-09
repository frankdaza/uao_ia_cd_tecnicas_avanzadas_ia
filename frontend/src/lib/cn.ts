import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Combina clases CSS con soporte de Tailwind merge. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
