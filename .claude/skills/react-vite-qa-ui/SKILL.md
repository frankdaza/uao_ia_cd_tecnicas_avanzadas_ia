---
name: react-vite-qa-ui
description: Construye la interfaz web Q&A (M1) y agente M2 (auth, SSE /api/agente/stream) con React 19 + Vite 8 + TypeScript 6 + Tailwind v4 + shadcn/ui + streaming. Usar al crear o modificar frontend/ o integracion con FastAPI.
---

# Interfaz Q&A con React 19 + Vite 8 + shadcn/ui

> Mantener el mismo contenido en `.cursor/skills/react-vite-qa-ui/` y `.claude/skills/react-vite-qa-ui/`.

## Stack tecnologico

| Capa | Tecnologia | Rol |
| --- | --- | --- |
| Build | Vite 8 + pnpm 10 | Bundler y gestor de paquetes |
| UI framework | React 19 + TypeScript 6 strict | Componentes y logica |
| Estilos | Tailwind CSS v4 + tailwindcss-animate | Utilidades CSS y animaciones |
| Componentes | shadcn/ui (Radix UI + lucide-react) | Sistema de diseno accesible |
| Datos del servidor | @tanstack/react-query v5 | Cache y sincronizacion |
| Streaming | fetch + ReadableStream + TextDecoderStream | SSE con POST body |
| SDK AI | ai + @ai-sdk/react (Vercel AI SDK) | useChat y transport personalizado |
| Temas | next-themes | Modo claro/oscuro persistente |
| Notificaciones | sonner | Toasts |
| Markdown | react-markdown + remark-gfm + shiki | Render enriquecido |
| Validacion | zod | Tipos inferidos desde esquemas |

## Patron de streaming SSE (critico)

`EventSource` nativo del navegador **no soporta POST con body JSON**. Usar `fetch` con `ReadableStream`:

```typescript
// frontend/src/lib/sseClient.ts
export async function streamQa(
  endpoint: string,
  peticion: QaPeticion,
  handlers: {
    onToken: (motor: string, texto: string) => void
    onFuentes: (fuentes: FuenteBm25[]) => void
    onFinal: (motor: string, meta: MetadatosFinal) => void
    onError: (mensaje: string) => void
  }
): Promise<void> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(peticion),
  })
  const reader = response.body!.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += value
    // parsear lineas SSE del buffer
    const lineas = buffer.split('\n')
    buffer = lineas.pop() ?? ''
    for (const linea of lineas) {
      if (linea.startsWith('data: ')) {
        const evento = JSON.parse(linea.slice(6))
        if (evento.tipo === 'token') handlers.onToken(evento.motor, evento.texto)
        else if (evento.tipo === 'fuentes') handlers.onFuentes(evento.fuentes)
        else if (evento.tipo === 'final') handlers.onFinal(evento.motor, evento)
        else if (evento.tipo === 'error') handlers.onError(evento.mensaje)
      }
    }
  }
}
```

## Estructura de carpetas requerida

```
frontend/src/
  features/
    chat/
      Chat.tsx              # contenedor principal; llama a streamQa
      MessageList.tsx       # lista scrollable con auto-scroll
      MessageBubble.tsx     # burbuja usuario/asistente con Markdown
      ChatInput.tsx         # textarea + boton Enviar
      DualResponseView.tsx  # dos columnas Ollama | OpenAI
      SourcesPanel.tsx      # cards de fuentes BM25
    settings/
      SettingsPanel.tsx
      ModelSelector.tsx
      SystemPromptEditor.tsx
  components/
    ui/                     # shadcn/ui generados por CLI
    AppShell.tsx            # layout principal
    ThemeToggle.tsx
  hooks/
    useModels.ts            # React Query: GET /api/modelos
    useReloadCorpus.ts      # React Query mutation: POST /api/recargar-corpus
  lib/
    api.ts                  # fetch tipado para endpoints sincronicos
    sseClient.ts            # streaming SSE con fetch + ReadableStream
    schemas.ts              # zod schemas + tipos inferidos
    cn.ts                   # utilidad clsx + tailwind-merge
  styles/
    globals.css             # @import "tailwindcss"; tokens CSS
```

## Paleta institucional Valle del Lili

```css
/* frontend/src/styles/globals.css */
@import "tailwindcss";

:root {
  --color-primary: #6B21A8;        /* morado institucional */
  --color-primary-light: #9333EA;
  --color-secondary: #0D9488;      /* teal complementario */
  --color-secondary-light: #14B8A6;
  --color-background: #FFFFFF;
  --color-surface: #F8F7FF;
  --color-text: #1F1235;
}

.dark {
  --color-background: #0F0A1A;
  --color-surface: #1A1030;
  --color-text: #F0EAF8;
}
```

## Componente Chat (patron basico)

```tsx
// frontend/src/features/chat/Chat.tsx
import { useState, useRef } from 'react'
import { streamQa } from '@/lib/sseClient'
import { useSettings } from '@/features/settings/SettingsContext'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const settings = useSettings()

  const handleSubmit = async (pregunta: string) => {
    setIsStreaming(true)
    const id = crypto.randomUUID()
    setMessages(prev => [
      ...prev,
      { id, role: 'user', content: pregunta },
      { id: id + '-resp', role: 'assistant', content: '', isStreaming: true },
    ])

    await streamQa('/api/qa/stream', { pregunta, ...settings }, {
      onToken: (_, texto) => setMessages(prev =>
        prev.map(m => m.id === id + '-resp' ? { ...m, content: m.content + texto } : m)
      ),
      onFinal: (_, meta) => setMessages(prev =>
        prev.map(m => m.id === id + '-resp' ? { ...m, isStreaming: false, meta } : m)
      ),
      onError: mensaje => toast.error(mensaje),
      onFuentes: fuentes => { /* actualizar estado de fuentes */ },
    })
    setIsStreaming(false)
  }

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      <ChatInput onSubmit={handleSubmit} disabled={isStreaming} />
    </div>
  )
}
```

## Render de Markdown con shiki

```tsx
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { createHighlighter } from 'shiki'

// En MessageBubble.tsx:
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{ code: CodeBlock }}
>
  {content}
</ReactMarkdown>
```

## Modo dual (DualResponseView) — historico M1

- Si aun existe en el codigo: activo cuando `settings.usarOllama && settings.usarOpenAI`.
- Consume `POST /api/qa/dual/stream`; eventos SSE distinguen `motor: 'ollama'` y `motor: 'openai'`.
- Layout: dos columnas CSS Grid `grid-cols-2 gap-4` cada una con su `MessageBubble` y badge de latencia.

## Modulo 2 — identificacion y agente

- **Auth**: carpeta `frontend/src/features/auth/` (`AuthScreen`, `AuthContext`): formulario documento + nombre; `POST /api/sesiones`; persistencia local acordada con backend (cookie HTTP-only y/o `X-Session-Id` + `localStorage` para flags, sin secretos en claro).
- **Chat**: transporte SSE hacia **`/api/agente/stream`** (no `EventSource` con POST; usar `fetch` + stream como en `streamQa`); handlers adicionales `onRouterThought` / `onTool` (o nombres en ingles en codigo: `onPensamiento`, `onHerramienta`) ademas de `onToken`, `onFuentes`, `onFinal`, `onError`.
- **Fuentes RAG**: panel de fuentes con `archivo`, `titulo`, `sourceUrl`, `score` (Qdrant), distinto de fuentes BM25 del M1.
- Backend y contrato SSE: skill **`fastapi-sse-api`** + **`agente-modulo-2`**.

## Textos de UI

- Todos los textos visibles al usuario en **espanol latinoamericano** (pueden llevar tildes).
- Placeholder del textarea: `'¿Cuál es tu pregunta sobre la Fundación Valle del Lili?'`
- Boton enviar: `'Enviar'` / `'Pensando...'` durante streaming.
- Labels de modelos: `'Modelo Ollama'`, `'Modelo OpenAI'`.

## Ejecucion del frontend

```bash
pnpm --dir frontend install
pnpm --dir frontend dev        # localhost:5173 (proxy /api -> localhost:8000)
pnpm --dir frontend build      # genera frontend/dist/
pnpm --dir frontend test       # Vitest
pnpm --dir frontend test:e2e   # Playwright
```

## Referencia de reglas

- Estilos y convenciones: `.cursor/rules/frontend-style.mdc`
- Idioma: `.cursor/rules/language-conventions.mdc` (excepcion TS/JS)
- Stack completo: `.cursor/rules/project-stack.mdc`
