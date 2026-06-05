import { useQuery } from '@tanstack/react-query'
import { getAdminDashboard } from '@/lib/api'

const REFETCH_MS = 20_000

export function useAdminDashboard(enabled: boolean) {
  return useQuery({
    queryKey: ['dashboard', 'admin'],
    queryFn: getAdminDashboard,
    enabled,
    refetchInterval: REFETCH_MS,
    refetchOnWindowFocus: true,
  })
}
