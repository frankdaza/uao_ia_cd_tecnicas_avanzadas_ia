import { useEffect } from 'react'
import { AdminLayout } from '@/features/admin/AdminLayout'
import { AdminDashboardPage } from '@/features/admin/AdminDashboardPage'
import { AdminModelPage } from '@/features/admin/AdminModelPage'
import { AdminPromptsPage } from '@/features/admin/AdminPromptsPage'
import { AdminUsuariosPage } from '@/features/admin/AdminUsuariosPage'

type Props = {
  adminKey: string
  pathActual: string
  onNavigate: (ruta: string) => void
  onSalirAdmin: () => void
}

function segmentoAdmin(path: string): string {
  if (path === '/admin' || path === '/admin/') return 'inicio'
  const resto = path.replace(/^\/admin\/?/, '')
  const primero = resto.split('/')[0] ?? 'inicio'
  return primero === '' ? 'inicio' : primero
}

export function AdminRutas({ adminKey, pathActual, onNavigate, onSalirAdmin }: Props) {
  const seg = segmentoAdmin(pathActual)

  useEffect(() => {
    const permitidos = new Set(['inicio', 'modelo', 'prompts', 'usuarios'])
    if (!permitidos.has(seg)) onNavigate('/admin')
  }, [seg, onNavigate])

  const titulos: Record<string, string> = {
    inicio: 'Panel',
    modelo: 'Modelo y sampling',
    prompts: 'Prompts',
    usuarios: 'Usuarios registrados',
  }
  const titulo = titulos[seg] ?? 'Panel'

  return (
    <AdminLayout titulo={titulo} pathActual={pathActual} onNavigate={onNavigate} onSalirAdmin={onSalirAdmin}>
      {seg === 'inicio' ? <AdminDashboardPage adminKey={adminKey} /> : null}
      {seg === 'modelo' ? <AdminModelPage adminKey={adminKey} /> : null}
      {seg === 'prompts' ? <AdminPromptsPage adminKey={adminKey} /> : null}
      {seg === 'usuarios' ? <AdminUsuariosPage adminKey={adminKey} /> : null}
    </AdminLayout>
  )
}
