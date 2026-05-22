/** Usuario del bot sin @ (Vite: ``VITE_TELEGRAM_BOT_USERNAME``). */
export function getTelegramBotUsername(): string | undefined {
  const raw = import.meta.env.VITE_TELEGRAM_BOT_USERNAME
  if (typeof raw !== 'string' || !raw.trim()) {
    return undefined
  }
  return raw.trim().replace(/^@/, '')
}

/** Deep link ``t.me/{bot}?start={codigo}`` para emparejamiento. */
export function buildTelegramStartLink(codigo: string): string | undefined {
  const bot = getTelegramBotUsername()
  if (!bot) {
    return undefined
  }
  return `https://t.me/${encodeURIComponent(bot)}?start=${encodeURIComponent(codigo)}`
}
