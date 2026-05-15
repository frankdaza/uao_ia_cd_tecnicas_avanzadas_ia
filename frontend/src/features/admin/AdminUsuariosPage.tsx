import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getAdminUsuarios } from '@/lib/adminApi'

type Props = {
  adminKey: string
}

const PAGE = 15

export function AdminUsuariosPage({ adminKey }: Props) {
  const [offset, setOffset] = useState(0)
  const q = useQuery({
    queryKey: ['admin', 'usuarios', adminKey, offset],
    queryFn: () => getAdminUsuarios(adminKey, { limit: PAGE, offset }),
  })

  if (q.isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    )
  }
  if (q.isError) {
    return <p className="text-sm text-destructive">No se pudo cargar el listado de usuarios.</p>
  }

  const data = q.data
  if (!data) {
    return <p className="text-sm text-destructive">Sin datos.</p>
  }

  const ultimaPagina = data.offset + data.items.length >= data.total

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Total: <strong className="text-foreground">{data.total}</strong> — mostrando {data.items.length} filas.
      </p>
      <div className="rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Documento</TableHead>
              <TableHead>Alta</TableHead>
              <TableHead>Último acceso</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No hay filas en esta página.
                </TableCell>
              </TableRow>
            ) : (
              data.items.map((u) => (
                <TableRow key={u.id}>
                  <TableCell>{u.nombre}</TableCell>
                  <TableCell className="font-mono text-xs">{u.documento_identidad_enmascarado}</TableCell>
                  <TableCell className="text-muted-foreground">{formatearFecha(u.created_at)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {u.last_login_at ? formatearFecha(u.last_login_at) : '—'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={offset === 0}
          onClick={() => setOffset((o) => Math.max(0, o - PAGE))}
          aria-label="Página anterior de usuarios"
        >
          Anterior
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={ultimaPagina}
          onClick={() => setOffset((o) => o + PAGE)}
          aria-label="Página siguiente de usuarios"
        >
          Siguiente
        </Button>
      </div>
    </div>
  )
}

function formatearFecha(iso: string) {
  try {
    return new Intl.DateTimeFormat('es-CO', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso))
  } catch {
    return iso
  }
}
