import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { postRecargarCorpus } from '@/lib/api'

/** Mutación que recarga el índice BM25 e invalida la cache de modelos. */
export function useReloadCorpus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: postRecargarCorpus,
    onSuccess: (data) => {
      toast.success(data.mensaje)
      void queryClient.invalidateQueries({ queryKey: ['modelos'] })
    },
    onError: (error: Error) => {
      toast.error(`Error al recargar el corpus: ${error.message}`)
    },
  })
}
