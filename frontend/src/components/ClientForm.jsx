import { useState } from 'react'
import axios from 'axios'

const field = (label, name, type = 'text', required = true) => ({ label, name, type, required })

const TEXT_FIELDS = [
  field('Project Name', 'project_name'),
  field('Merchant ID (mid)', 'mid'),
  field('Package Name', 'package_name'),
  field('App Name', 'app_name'),
  field('Shop Domain', 'shop_domain'),
  field('API Key', 'api_key'),
  field('Access Token', 'access_token'),
]

export default function ClientForm({ onStatusChange }) {
  const [perScreen, setPerScreen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [previewVisible, setPreviewVisible] = useState(true)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    onStatusChange({ state: 'loading', message: 'Creating project...' })

    const form = e.target
    const data = new FormData()

    TEXT_FIELDS.forEach(({ name }) => data.append(name, form[name].value))
    data.append('preview_visible', previewVisible)
    data.append('app_icon', form.app_icon.files[0])
    data.append('header_logo', form.header_logo.files[0])

    if (form.google_services_json.files[0])
      data.append('google_services_json', form.google_services_json.files[0])

    if (perScreen) {
      const screens = ['logo_userprofile', 'logo_account_details', 'logo_login', 'logo_otp']
      screens.forEach(name => {
        if (form[name]?.files[0]) data.append(name, form[name].files[0])
      })
    }

    try {
      const res = await axios.post('/api/create-client', data)
      onStatusChange({ state: 'success', message: res.data.message, repoUrl: res.data.repo_url })
    } catch (err) {
      const detail = err.response?.data?.detail || err.message
      onStatusChange({ state: 'error', message: `Error: ${detail}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {TEXT_FIELDS.map(({ label, name }) => (
        <label key={name} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>{label}</span>
          <input name={name} required style={{ padding: 8, fontSize: 14 }} />
        </label>
      ))}

      <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input
          type="checkbox"
          checked={previewVisible}
          onChange={e => setPreviewVisible(e.target.checked)}
        />
        Preview Visible (menuData!!.previewvislible = View.VISIBLE)
      </label>

      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span>App Icon (high-res, 1024×1024 recommended) *</span>
        <input type="file" name="app_icon" accept="image/*" required />
      </label>

      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span>Header Logo (default for all screens) *</span>
        <input type="file" name="header_logo" accept="image/*" required />
      </label>

      <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input type="checkbox" checked={perScreen} onChange={e => setPerScreen(e.target.checked)} />
        Different logo per screen?
      </label>

      {perScreen && (
        <div style={{ paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[
            ['logo_userprofile', 'User Profile screen logo'],
            ['logo_account_details', 'Account Details screen logo'],
            ['logo_login', 'Login screen logo'],
            ['logo_otp', 'OTP Verification screen logo'],
          ].map(([name, label]) => (
            <label key={name} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span>{label} (leave empty to use default)</span>
              <input type="file" name={name} accept="image/*" />
            </label>
          ))}
        </div>
      )}

      <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span>google-services.json (optional — uses base repo default if omitted)</span>
        <input type="file" name="google_services_json" accept=".json" />
      </label>

      <button
        type="submit"
        disabled={loading}
        style={{ padding: '12px 24px', fontSize: 16, cursor: loading ? 'not-allowed' : 'pointer' }}
      >
        {loading ? 'Creating…' : 'Create Client Project'}
      </button>
    </form>
  )
}
