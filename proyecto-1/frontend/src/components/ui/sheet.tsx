import type { ReactNode } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Button } from '@/components/ui/button'

interface SheetProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  title: string
  /** Texto accesible breve (Radix DialogDescription); por defecto panel de navegación. */
  description?: string
  children: ReactNode
  side?: 'left' | 'right'
}

/** Panel lateral deslizable (solo móvil) basado en Radix Dialog. */
export function Sheet({
  open,
  onOpenChange,
  title,
  description = 'Panel lateral de navegación',
  children,
  side = 'left',
}: SheetProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40 data-[state=open]:animate-in data-[state=closed]:animate-out fade-in-0 zoom-out-95" />
        <Dialog.Content
          className={cn(
            'fixed z-50 outline-none shadow-lg bg-[var(--color-surface)] border border-[var(--border)] overflow-hidden flex flex-col',
            side === 'left' ? 'left-0 top-0 h-full w-[min(19rem,90vw)]' : 'right-0 top-0 h-full',
            'data-[state=open]:animate-in data-[state=closed]:animate-out fade-in zoom-in slide-in-from-left-2',
          )}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] shrink-0">
            <Dialog.Title className="text-sm font-semibold">{title}</Dialog.Title>
            <Dialog.Close asChild>
              <Button variant="ghost" size="icon" aria-label="Cerrar configuración">
                <X className="h-4 w-4" />
              </Button>
            </Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">{description}</Dialog.Description>
          <div className="flex-1 min-h-0">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
