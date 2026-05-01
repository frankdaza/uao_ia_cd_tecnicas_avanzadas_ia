import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'
import { codeToHtml } from 'shiki'

interface MarkdownCodeBlockProps {
  code: string
  language: string
}

/** Bloque de código con resaltado Shiki (temas claro/oscuro según next-themes). */
export function MarkdownCodeBlock({ code, language }: MarkdownCodeBlockProps) {
  const { resolvedTheme } = useTheme()
  const [html, setHtml] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const theme = resolvedTheme === 'dark' ? 'github-dark' : 'github-light'
    const lang = language.trim() || 'txt'

    codeToHtml(code, { lang, theme })
      .then((h) => {
        if (!cancelled) setHtml(h)
      })
      .catch(() => {
        if (!cancelled) setHtml(null)
      })

    return () => {
      cancelled = true
    }
  }, [code, language, resolvedTheme])

  if (!html) {
    return (
      <pre className="rounded-lg border border-[var(--border)] bg-[var(--color-surface-2)] p-3 text-xs overflow-x-auto">
        <code className="font-mono">{code}</code>
      </pre>
    )
  }

  return (
    <div
      className="rounded-lg border border-[var(--border)] overflow-x-auto [&_pre]:!m-0 [&_pre]:!bg-transparent"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
