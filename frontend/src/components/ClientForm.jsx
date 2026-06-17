import { useState } from 'react'
import axios from 'axios'

const TEXT_FIELDS_TOP = [
  { label: 'Project Name',      name: 'project_name', placeholder: 'Acme Store' },
  { label: 'Merchant ID',       name: 'mid',          placeholder: 'acme001' },
  { label: 'Package Name',      name: 'package_name', placeholder: 'com.acme.store' },
  { label: 'App Name',          name: 'app_name',     placeholder: 'Acme' },
]

const API_FIELDS = [
  { label: 'Shop Domain',  name: 'shop_domain',   placeholder: 'acme.myshopify.com' },
  { label: 'API Key',      name: 'api_key',        placeholder: 'API key' },
  { label: 'Access Token', name: 'access_token',   placeholder: 'shpat_…' },
]

const ALL_TEXT_FIELDS = [...TEXT_FIELDS_TOP, ...API_FIELDS]

const PER_SCREEN_SLOTS = [
  { name: 'logo_userprofile',    label: 'User Profile' },
  { name: 'logo_account_details',label: 'Account Details' },
  { name: 'logo_login',          label: 'Login' },
  { name: 'logo_otp',            label: 'OTP Verification' },
]

function FileInput({ name, accept, required, label, hint }) {
  const [fileName, setFileName] = useState(null)
  return (
    <label className="file-label">
      <input
        type="file"
        name={name}
        accept={accept}
        required={required}
        onChange={e => setFileName(e.target.files[0]?.name || null)}
      />
      <span className="file-icon">📎</span>
      <span className="file-text">
        <span className="file-name">{fileName || label}</span>
        <span className="file-hint">{fileName ? '✓ selected' : hint}</span>
      </span>
    </label>
  )
}

export default function ClientForm({ onStatusChange }) {
  const [perScreen, setPerScreen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [previewVisible, setPreviewVisible] = useState(true)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    onStatusChange({ state: 'loading', message: 'Creating project…' })

    const form = e.target
    const data = new FormData()

    ALL_TEXT_FIELDS.forEach(({ name }) => data.append(name, form[name].value))
    data.append('preview_visible', String(previewVisible))
    data.append('app_icon', form.app_icon.files[0])
    data.append('header_logo', form.header_logo.files[0])

    if (form.google_services_json.files[0])
      data.append('google_services_json', form.google_services_json.files[0])

    if (perScreen) {
      PER_SCREEN_SLOTS.forEach(({ name }) => {
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
    <form onSubmit={handleSubmit}>

      {/* Project Details */}
      <div className="section">
        <p className="section-title">Project Details</p>
        <div className="field-row">
          {TEXT_FIELDS_TOP.slice(0, 2).map(({ label, name, placeholder }) => (
            <div className="field" key={name}>
              <span className="label">{label}</span>
              <input className="input" name={name} placeholder={placeholder} required />
            </div>
          ))}
        </div>
        <div className="field-row">
          {TEXT_FIELDS_TOP.slice(2).map(({ label, name, placeholder }) => (
            <div className="field" key={name}>
              <span className="label">{label}</span>
              <input className="input" name={name} placeholder={placeholder} required />
            </div>
          ))}
        </div>
      </div>

      {/* API Credentials */}
      <div className="section">
        <p className="section-title">API Credentials</p>
        {API_FIELDS.map(({ label, name, placeholder }) => (
          <div className="field" key={name}>
            <span className="label">{label}</span>
            <input className="input" name={name} placeholder={placeholder} required />
          </div>
        ))}
        <div className="field" style={{ marginTop: 14 }}>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={previewVisible}
              onChange={e => setPreviewVisible(e.target.checked)}
            />
            <span className="toggle-label">Show preview menu item</span>
          </label>
        </div>
      </div>

      {/* Assets */}
      <div className="section">
        <p className="section-title">Assets</p>

        <div className="field">
          <span className="label">App Icon <span className="label-optional">(1024×1024 recommended)</span></span>
          <FileInput name="app_icon" accept="image/*" required label="Choose app icon…" hint="PNG, JPG — will be resized to all densities" />
        </div>

        <div className="field">
          <span className="label">Header Logo</span>
          <FileInput name="header_logo" accept="image/*" required label="Choose header logo…" hint="Applied to all 4 screens by default" />
        </div>

        <div className="field">
          <label className="toggle-row">
            <input type="checkbox" checked={perScreen} onChange={e => setPerScreen(e.target.checked)} />
            <span className="toggle-label">Use different logo per screen</span>
          </label>
          {perScreen && (
            <div className="per-screen-grid">
              {PER_SCREEN_SLOTS.map(({ name, label }) => (
                <div className="field" key={name}>
                  <span className="label">{label}</span>
                  <FileInput name={name} accept="image/*" label="Choose…" hint="optional" />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="field">
          <span className="label">google-services.json <span className="label-optional">(optional)</span></span>
          <FileInput name="google_services_json" accept=".json" label="Choose JSON file…" hint="Uses base repo default if omitted" />
        </div>
      </div>

      {/* Submit */}
      <div className="section">
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Creating project…' : 'Create Client Project'}
        </button>
      </div>

    </form>
  )
}
