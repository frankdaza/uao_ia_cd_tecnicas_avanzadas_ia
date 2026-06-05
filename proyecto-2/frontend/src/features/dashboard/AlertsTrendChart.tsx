import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import type { PuntoSerieAlertas } from '@/lib/schemas'

const chartConfig = {
  cantidad: {
    label: 'Alertas',
    color: 'var(--color-accent)',
  },
}

interface AlertsTrendChartProps {
  serie: PuntoSerieAlertas[]
}

function formatFechaCorta(fechaIso: string): string {
  const d = new Date(`${fechaIso}T12:00:00`)
  return d.toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric' })
}

/** Tendencia de alertas creadas en los últimos 7 días. */
export function AlertsTrendChart({ serie }: AlertsTrendChartProps) {
  const data = serie.map((p) => ({
    fecha: p.fecha,
    cantidad: p.cantidad,
    etiqueta: formatFechaCorta(p.fecha),
  }))

  return (
    <Card className="col-span-full lg:col-span-2">
      <CardHeader>
        <CardTitle>Tendencia de alertas</CardTitle>
        <CardDescription>Alertas creadas por día (últimos 7 días)</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[220px] w-full">
          <AreaChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
            <defs>
              <linearGradient id="fillAlertas" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="etiqueta"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              fontSize={11}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              width={32}
              fontSize={11}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="cantidad"
              stroke="var(--color-accent)"
              strokeWidth={2}
              fill="url(#fillAlertas)"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
