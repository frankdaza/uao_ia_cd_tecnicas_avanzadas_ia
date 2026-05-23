import { AlertasBandejaPage } from './AlertasBandejaPage'
import { CasoSeguimientoDetallePage } from './CasoSeguimientoDetallePage'
import { CasosSeguimientoListPage } from './CasosSeguimientoListPage'
import { parseCasoIdFromPath, SEGUIMIENTO_CASOS_PATH, SEGUIMIENTO_PATH } from './seguimientoPaths'

interface SeguimientoRoutesProps {
  path: string
  onNavigate: (path: string) => void
}

/** Enrutamiento interno bajo ``/seguimiento``. */
export function SeguimientoRoutes({ path, onNavigate }: SeguimientoRoutesProps) {
  const casoId = parseCasoIdFromPath(path)
  if (casoId) {
    return <CasoSeguimientoDetallePage casoId={casoId} onNavigate={onNavigate} />
  }

  if (path === SEGUIMIENTO_CASOS_PATH) {
    return <CasosSeguimientoListPage onNavigate={onNavigate} />
  }

  if (path === SEGUIMIENTO_PATH || path.startsWith(`${SEGUIMIENTO_PATH}/`)) {
    return <AlertasBandejaPage onNavigate={onNavigate} />
  }

  return <AlertasBandejaPage onNavigate={onNavigate} />
}
