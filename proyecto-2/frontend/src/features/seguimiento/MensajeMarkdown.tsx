import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MensajeMarkdownProps {
  children: string
}

/** Render Markdown en burbujas del bot (hilo de seguimiento). */
export function MensajeMarkdown({ children }: MensajeMarkdownProps) {
  if (!children.trim()) {
    return null
  }

  return (
    <div className="mensaje-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
