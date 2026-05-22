import { ProcedimientoDetallePage } from './ProcedimientoDetallePage'
import { ProcedimientoNuevoPage } from './ProcedimientoNuevoPage'
import { ProcedimientosListPage } from './ProcedimientosListPage'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

interface AdminProcedimientosRoutesProps {
  path: string
  onNavigate: (path: string) => void
}

/** Enrutamiento interno bajo ``/admin/procedimientos``. */
export function AdminProcedimientosRoutes({ path, onNavigate }: AdminProcedimientosRoutesProps) {
  if (path === '/admin/procedimientos/nuevo') {
    return <ProcedimientoNuevoPage onNavigate={onNavigate} />
  }

  const detalleMatch = path.match(/^\/admin\/procedimientos\/([^/]+)$/)
  if (detalleMatch && detalleMatch[1] !== 'nuevo' && UUID_RE.test(detalleMatch[1])) {
    return <ProcedimientoDetallePage id={detalleMatch[1]} onNavigate={onNavigate} />
  }

  return <ProcedimientosListPage onNavigate={onNavigate} />
}
