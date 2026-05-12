import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { waitFor } from '@testing-library/react'
import { SETTINGS_DEFAULTS, SettingsProvider, useSettings } from '@/features/settings/SettingsContext'

describe('SettingsContext persistencia', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  function MuestraTemperatura() {
    const { settings } = useSettings()
    return <span data-testid="temperatura">{settings.temperatura}</span>
  }

  function BotonCambiarTemperatura() {
    const { updateSettings } = useSettings()
    return (
      <button type="button" onClick={() => updateSettings({ temperatura: 0.9 })}>
        subir-temperatura
      </button>
    )
  }

  it('hidrata valores desde localStorage', () => {
    localStorage.setItem('fvl-settings-v2', JSON.stringify({ temperatura: 0.5 }))
    render(
      <SettingsProvider>
        <MuestraTemperatura />
      </SettingsProvider>,
    )
    expect(screen.getByTestId('temperatura')).toHaveTextContent('0.5')
    expect(screen.getByTestId('temperatura')).not.toHaveTextContent(String(SETTINGS_DEFAULTS.temperatura))
  })

  it('persiste tras cambios posteriores al montaje', async () => {
    const user = userEvent.setup()
    render(
      <SettingsProvider>
        <MuestraTemperatura />
        <BotonCambiarTemperatura />
      </SettingsProvider>,
    )

    await user.click(screen.getByRole('button', { name: /subir-temperatura/i }))
    await waitFor(() => {
      const raw = localStorage.getItem('fvl-settings-v2')
      expect(raw).toBeTruthy()
      expect(JSON.parse(raw as string).temperatura).toBe(0.9)
    })
    expect(screen.getByTestId('temperatura')).toHaveTextContent('0.9')
  })
})
