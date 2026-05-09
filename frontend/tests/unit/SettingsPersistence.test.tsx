import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { waitFor } from '@testing-library/react'
import { SETTINGS_DEFAULTS, SettingsProvider, useSettings } from '@/features/settings/SettingsContext'

describe('SettingsContext persistencia', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  function MuestraNumCtx() {
    const { settings } = useSettings()
    return <span data-testid="num-ctx">{settings.numCtx}</span>
  }

  function BotonPersistirAlto() {
    const { updateSettings } = useSettings()
    return (
      <button type="button" onClick={() => updateSettings({ numCtx: 12345 })}>
        subir-num-ctx
      </button>
    )
  }

  it('hidrata valores desde localStorage', () => {
    localStorage.setItem('fvl-settings-v1', JSON.stringify({ numCtx: 7777 }))
    render(
      <SettingsProvider>
        <MuestraNumCtx />
      </SettingsProvider>,
    )
    expect(screen.getByTestId('num-ctx')).toHaveTextContent('7777')
    expect(screen.getByTestId('num-ctx')).not.toHaveTextContent(String(SETTINGS_DEFAULTS.numCtx))
  })

  it('persiste tras cambios posteriores al montaje', async () => {
    const user = userEvent.setup()
    render(
      <SettingsProvider>
        <MuestraNumCtx />
        <BotonPersistirAlto />
      </SettingsProvider>,
    )

    await user.click(screen.getByRole('button', { name: /subir-num-ctx/i }))
    await waitFor(() => {
      const raw = localStorage.getItem('fvl-settings-v1')
      expect(raw).toBeTruthy()
      expect(JSON.parse(raw as string).numCtx).toBe(12345)
    })
    expect(screen.getByTestId('num-ctx')).toHaveTextContent('12345')
  })
})
