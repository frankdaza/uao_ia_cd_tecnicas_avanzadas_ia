import { useId, useMemo, useState } from 'react'
import { Check, ChevronsUpDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/cn'
import type { TipoProcedimientoOpcion } from '@/lib/schemas'
import { etiquetaTipoProcedimiento, filtrarTiposProcedimiento } from './tipoProcedimientoComboboxUtils'

interface TipoProcedimientoComboboxProps {
  id?: string
  value: TipoProcedimientoOpcion | null
  onChange: (tipo: TipoProcedimientoOpcion | null) => void
  items: TipoProcedimientoOpcion[]
  disabled?: boolean
  isLoading?: boolean
}

/** Combobox con filtro para elegir tipo de procedimiento del catálogo staff. */
export function TipoProcedimientoCombobox({
  id: idProp,
  value,
  onChange,
  items,
  disabled = false,
  isLoading = false,
}: TipoProcedimientoComboboxProps) {
  const generatedId = useId()
  const triggerId = idProp ?? generatedId
  const listId = `${triggerId}-listbox`
  const [open, setOpen] = useState(false)
  const [busqueda, setBusqueda] = useState('')

  const filtrados = useMemo(
    () => filtrarTiposProcedimiento(items, busqueda),
    [items, busqueda],
  )

  const deshabilitado = disabled || isLoading || items.length === 0

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setBusqueda('')
      }}
    >
      <PopoverTrigger asChild>
        <Button
          id={triggerId}
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          disabled={deshabilitado}
          className={cn(
            'h-10 w-full justify-between font-normal',
            !value && 'text-[var(--color-text-subtle)]',
          )}
        >
          <span className="truncate">
            {isLoading
              ? 'Cargando procedimientos…'
              : value
                ? etiquetaTipoProcedimiento(value)
                : 'Seleccione un procedimiento…'}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" aria-hidden />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="p-0" align="start">
        <Command shouldFilter={false} aria-labelledby={triggerId}>
          <CommandInput
            placeholder="Buscar por nombre o código…"
            value={busqueda}
            onValueChange={setBusqueda}
          />
          <CommandList id={listId}>
            <CommandEmpty>No hay coincidencias.</CommandEmpty>
            <CommandGroup>
              {filtrados.map((t) => (
                <CommandItem
                  key={t.id}
                  value={t.id}
                  onSelect={() => {
                    onChange(t)
                    setOpen(false)
                    setBusqueda('')
                  }}
                >
                  <Check
                    className={cn(
                      'mr-2 h-4 w-4',
                      value?.id === t.id ? 'opacity-100' : 'opacity-0',
                    )}
                    aria-hidden
                  />
                  <span className="truncate">{etiquetaTipoProcedimiento(t)}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
