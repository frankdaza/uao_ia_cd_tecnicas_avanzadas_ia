import { useQuery } from '@tanstack/react-query'
import { getModelos } from '@/lib/api'
import type { ModelosRespuesta } from '@/lib/schemas'

/** Obtiene los modelos disponibles por motor con cache de 30 segundos. */
export function useModels(): {
  data: ModelosRespuesta | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
} {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['modelos'],
    queryFn: getModelos,
    staleTime: 30_000,
    retry: 2,
  })
  return { data, isLoading, isError, error }
}
