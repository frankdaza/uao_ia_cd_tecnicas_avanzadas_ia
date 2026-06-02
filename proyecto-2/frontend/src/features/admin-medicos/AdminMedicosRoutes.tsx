import { MedicoDetallePage } from './MedicoDetallePage'
import { MedicoNuevoPage } from './MedicoNuevoPage'
import { MedicosListPage } from './MedicosListPage'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

interface AdminMedicosRoutesProps {
  path: string
  onNavigate: (path: string) => void
}

/** Enrutamiento interno bajo ``/admin/medicos``. */
export function AdminMedicosRoutes({ path, onNavigate }: AdminMedicosRoutesProps) {
  if (path === '/admin/medicos/nuevo') {
    return <MedicoNuevoPage onNavigate={onNavigate} />
  }

  const detalleMatch = path.match(/^\/admin\/medicos\/([^/]+)$/)
  if (detalleMatch && detalleMatch[1] !== 'nuevo' && UUID_RE.test(detalleMatch[1])) {
    return <MedicoDetallePage id={detalleMatch[1]} onNavigate={onNavigate} />
  }

  return <MedicosListPage onNavigate={onNavigate} />
}
