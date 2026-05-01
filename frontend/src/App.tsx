import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { SettingsProvider } from '@/features/settings/SettingsContext'
import { AppShell } from '@/components/AppShell'
import { SettingsPanel } from '@/features/settings/SettingsPanel'
import { Chat } from '@/features/chat/Chat'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <TooltipProvider delayDuration={300}>
          <SettingsProvider>
            <AppShell sidebar={<SettingsPanel />}>
              <Chat />
            </AppShell>
            <Toaster richColors position="top-right" />
          </SettingsProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
