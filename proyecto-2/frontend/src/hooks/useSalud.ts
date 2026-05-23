import { useQuery } from '@tanstack/react-query'
import { getSalud } from '@/lib/api'

/** Verifica periódicamente si la API TAAM está disponible. */
export function useSalud() {
  return useQuery({
    queryKey: ['salud'],
    queryFn: getSalud,
    staleTime: 10_000,
    refetchInterval: 15_000,
    retry: 1,
  })
}
