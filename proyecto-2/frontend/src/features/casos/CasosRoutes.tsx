import { CASOS_NUEVO_PATH } from './casosPaths'
import { CasoNuevoPage } from './CasoNuevoPage'
import { CasosListPage } from './CasosListPage'

interface CasosRoutesProps {
  path: string
  onNavigate: (path: string) => void
}

/** Enrutamiento interno bajo ``/casos``. */
export function CasosRoutes({ path, onNavigate }: CasosRoutesProps) {
  if (path === CASOS_NUEVO_PATH) {
    return <CasoNuevoPage onNavigate={onNavigate} />
  }

  return <CasosListPage onNavigate={onNavigate} />
}
