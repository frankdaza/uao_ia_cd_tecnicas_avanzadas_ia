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
import type { MedicoOpcion } from '@/lib/schemas'
import { etiquetaMedico, filtrarMedicos } from './medicoComboboxUtils'

interface MedicoComboboxProps {
  id?: string
  value: MedicoOpcion | null
  onChange: (medico: MedicoOpcion | null) => void
  items: MedicoOpcion[]
  disabled?: boolean
  isLoading?: boolean
}

/** Combobox con filtro para elegir cirujano del catálogo staff. */
export function MedicoCombobox({
  id: idProp,
  value,
  onChange,
  items,
  disabled = false,
  isLoading = false,
}: MedicoComboboxProps) {
  const generatedId = useId()
  const triggerId = idProp ?? generatedId
  const listId = `${triggerId}-listbox`
  const [open, setOpen] = useState(false)
  const [busqueda, setBusqueda] = useState('')

  const filtrados = useMemo(() => filtrarMedicos(items, busqueda), [items, busqueda])

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
              ? 'Cargando médicos…'
              : value
                ? etiquetaMedico(value)
                : 'Seleccione un cirujano…'}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" aria-hidden />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="p-0" align="start">
        <Command shouldFilter={false} aria-labelledby={triggerId}>
          <CommandInput
            placeholder="Buscar por nombre, código o especialidad…"
            value={busqueda}
            onValueChange={setBusqueda}
          />
          <CommandList id={listId}>
            <CommandEmpty>No hay coincidencias.</CommandEmpty>
            <CommandGroup>
              {filtrados.map((m) => (
                <CommandItem
                  key={m.codigo_registro}
                  value={m.codigo_registro}
                  onSelect={() => {
                    onChange(m)
                    setOpen(false)
                    setBusqueda('')
                  }}
                >
                  <Check
                    className={cn(
                      'mr-2 h-4 w-4',
                      value?.codigo_registro === m.codigo_registro ? 'opacity-100' : 'opacity-0',
                    )}
                    aria-hidden
                  />
                  <span className="truncate">{etiquetaMedico(m)}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
