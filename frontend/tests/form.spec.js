import { test, expect } from '@playwright/test'
import { Buffer } from 'buffer'

// Minimal 1×1 transparent PNG (67 bytes)
const TINY_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
)

const PNG_FILE = { name: 'test.png', mimeType: 'image/png', buffer: TINY_PNG }

const TEXT_FIELDS = [
  { label: 'Project Name', name: 'project_name', value: 'Acme Store' },
  { label: 'Merchant ID (mid)', name: 'mid', value: 'acme001' },
  { label: 'Package Name', name: 'package_name', value: 'com.acme.store' },
  { label: 'App Name', name: 'app_name', value: 'Acme' },
  { label: 'Shop Domain', name: 'shop_domain', value: 'acme.myshopify.com' },
  { label: 'API Key', name: 'api_key', value: 'apikey123' },
  { label: 'Access Token', name: 'access_token', value: 'shpat_abc' },
]

async function fillRequiredFields(page) {
  for (const { name, value } of TEXT_FIELDS) {
    await page.locator(`input[name="${name}"]`).fill(value)
  }
  await page.locator('input[name="app_icon"]').setInputFiles(PNG_FILE)
  await page.locator('input[name="header_logo"]').setInputFiles(PNG_FILE)
}

test.describe('Page structure', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows the page heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'New Client Project Setup' })).toBeVisible()
  })

  test('renders all 7 text fields', async ({ page }) => {
    for (const { name } of TEXT_FIELDS) {
      await expect(page.locator(`input[name="${name}"]`)).toBeVisible()
    }
  })

  test('renders app_icon and header_logo file inputs', async ({ page }) => {
    // File inputs are visually hidden inside styled label wrappers — check the wrapper
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="app_icon"]') })).toBeVisible()
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="header_logo"]') })).toBeVisible()
  })

  test('renders google_services_json file input', async ({ page }) => {
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="google_services_json"]') })).toBeVisible()
  })

  test('renders the submit button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Create Client Project' })).toBeVisible()
  })
})

test.describe('Preview visible toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('preview visible checkbox is checked by default', async ({ page }) => {
    await expect(page.locator('input[type="checkbox"]').first()).toBeChecked()
  })

  test('unchecking preview visible updates state', async ({ page }) => {
    const checkbox = page.locator('input[type="checkbox"]').first()
    await checkbox.uncheck()
    await expect(checkbox).not.toBeChecked()
  })

  test('re-checking preview visible restores state', async ({ page }) => {
    const checkbox = page.locator('input[type="checkbox"]').first()
    await checkbox.uncheck()
    await checkbox.check()
    await expect(checkbox).toBeChecked()
  })
})

test.describe('Per-screen logo toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('per-screen logo slots are hidden by default', async ({ page }) => {
    await expect(page.locator('input[name="logo_userprofile"]')).not.toBeVisible()
    await expect(page.locator('input[name="logo_account_details"]')).not.toBeVisible()
    await expect(page.locator('input[name="logo_login"]')).not.toBeVisible()
    await expect(page.locator('input[name="logo_otp"]')).not.toBeVisible()
  })

  test('toggling "Use different logo per screen" reveals all 4 slots', async ({ page }) => {
    await page.getByLabel('Use different logo per screen').check()
    // Slots revealed — check wrapper labels (inputs are visually hidden inside them)
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="logo_userprofile"]') })).toBeVisible()
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="logo_account_details"]') })).toBeVisible()
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="logo_login"]') })).toBeVisible()
    await expect(page.locator('.file-label').filter({ has: page.locator('input[name="logo_otp"]') })).toBeVisible()
  })

  test('untoggling hides the per-screen slots again', async ({ page }) => {
    const toggle = page.getByLabel('Use different logo per screen')
    await toggle.check()
    await toggle.uncheck()
    await expect(page.locator('.per-screen-grid')).not.toBeVisible()
  })
})

test.describe('Form submission — success', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('/api/create-client', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          repo_url: 'https://github.com/testorg/acme001_Acme_Store',
          status: 'build_triggered',
          message: 'Build triggered — APK will be emailed when ready',
        }),
      }),
    )
    await page.goto('/')
  })

  test('shows loading state while request is in-flight', async ({ page }) => {
    let resolveRequest
    await page.route('/api/create-client', route => {
      return new Promise(res => { resolveRequest = () => res(route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ repo_url: 'https://github.com/org/repo', status: 'build_triggered', message: 'ok' }),
      })) })
    })

    await fillRequiredFields(page)
    const submitPromise = page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByRole('button', { name: 'Creating project…' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Creating project…' })).toBeDisabled()
    resolveRequest()
    await submitPromise
  })

  test('shows success status panel after submit', async ({ page }) => {
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByText('Build triggered — APK will be emailed when ready')).toBeVisible()
  })

  test('shows repo URL link in status panel on success', async ({ page }) => {
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByRole('link', { name: 'https://github.com/testorg/acme001_Acme_Store' })).toBeVisible()
  })

  test('repo URL link opens in new tab', async ({ page }) => {
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    const link = page.getByRole('link', { name: 'https://github.com/testorg/acme001_Acme_Store' })
    await expect(link).toHaveAttribute('target', '_blank')
  })

  test('button is re-enabled after successful submit', async ({ page }) => {
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByRole('button', { name: 'Create Client Project' })).toBeEnabled()
  })
})

test.describe('Form submission — error', () => {
  test('shows error status panel on 500 response', async ({ page }) => {
    await page.route('/api/create-client', route =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Clone failed: repository not found' }),
      }),
    )
    await page.goto('/')
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByText('Error: Clone failed: repository not found')).toBeVisible()
  })

  test('shows error status panel on 422 validation error', async ({ page }) => {
    await page.route('/api/create-client', route =>
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid package_name: must be like com.example.app' }),
      }),
    )
    await page.goto('/')
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByText('Error: Invalid package_name: must be like com.example.app')).toBeVisible()
  })

  test('button is re-enabled after error', async ({ page }) => {
    await page.route('/api/create-client', route =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'failed' }) }),
    )
    await page.goto('/')
    await fillRequiredFields(page)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByRole('button', { name: 'Create Client Project' })).toBeEnabled()
  })
})

test.describe('Per-screen logo submission', () => {
  test('per-screen logo files are sent when toggle is on', async ({ page }) => {
    let capturedBody = null
    await page.route('/api/create-client', async route => {
      capturedBody = route.request().postData()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ repo_url: 'https://github.com/org/repo', status: 'build_triggered', message: 'ok' }),
      })
    })
    await page.goto('/')
    await fillRequiredFields(page)
    await page.getByLabel('Use different logo per screen').check()
    await page.locator('input[name="logo_login"]').setInputFiles(PNG_FILE)
    await page.getByRole('button', { name: 'Create Client Project' }).click()
    await expect(page.getByText('ok', { exact: true })).toBeVisible()
    expect(capturedBody).toContain('logo_login')
  })
})
