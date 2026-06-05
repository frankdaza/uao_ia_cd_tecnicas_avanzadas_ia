import { useQuery } from '@tanstack/react-query'
import { getStaffDashboard } from '@/lib/api'

const REFETCH_MS = 20_000

export function useStaffDashboard() {
  return useQuery({
    queryKey: ['dashboard', 'staff'],
    queryFn: getStaffDashboard,
    refetchInterval: REFETCH_MS,
    refetchOnWindowFocus: true,
  })
}
