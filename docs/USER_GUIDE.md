# Android Client Setup — User Guide

This tool automates creating a new Android client app from the base project. Fill in a web form, click submit, and receive a built APK via email — no Android Studio or git required.

---

## One-Time Setup

Complete these steps once before using the tool for the first time.

### 1. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
```

### 3. Configure environment variables

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Open `.env` and fill in the three values:

| Variable | What to put |
|---|---|
| `GITHUB_TOKEN` | A GitHub Personal Access Token with `repo` scope. Create one at: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens |
| `GITHUB_ORG` | The GitHub organisation (or your username) where new client repos will be created |
| `BASE_ANDROID_REPO_URL` | The HTTPS URL of your base Android repo, e.g. `https://github.com/yourorg/base-android.git` |

### 4. Set up Google Drive (for APK delivery)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project (or use an existing one)
3. Enable the **Google Drive API**
4. Create a **Service Account** and download the JSON credentials file
5. In Google Drive, create a folder for APK storage and share it with the service account email address (give it **Editor** access)
6. Note the folder ID — it's the long string at the end of the folder's URL

### 5. Set up Gmail for notifications

1. Enable 2-Factor Authentication on the Gmail account you'll use for sending
2. Go to Google Account → Security → App passwords
3. Generate an app password for "Mail"

### 6. Add secrets to the base Android repo

In the base Android repo on GitHub, go to **Settings → Secrets and variables → Actions** and add these secrets:

| Secret name | Value |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full contents of the service account JSON file |
| `GOOGLE_DRIVE_FOLDER_ID` | The Drive folder ID from Step 4 |
| `GMAIL_USER` | The Gmail address used for sending |
| `GMAIL_APP_PASSWORD` | The app password from Step 5 |
| `NOTIFY_EMAIL` | The email address that should receive the APK link |

### 7. Update base package name

Open `backend/main.py` and update `BASE_PACKAGE_NAME` to match the `applicationId` in your base Android repo's `app/build.gradle`:

```python
BASE_PACKAGE_NAME = "com.yourorg.baseapp"  # change this
```

### 8. Verify logo drawable names (if needed)

If your base Android repo uses different drawable names for the header logo, update `backend/asset_replacer.py`:

```python
HEADER_LOGO_DRAWABLE_NAME = "header_logo"  # change to match your drawable name
```

---

## Starting the Tool

Open two terminal windows.

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

You should see: `Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

You should see: `Local: http://localhost:5173`

Open `http://localhost:5173` in your browser.

---

## Creating a New Client Project

### Form fields

Fill in each field:

| Field | Description | Example |
|---|---|---|
| **Project name** | Human-readable client name | `Acme Store` |
| **MID** | Merchant ID — used in the repo name and app config | `acme001` |
| **Package name** | Android package name (3 segments, lowercase) | `com.acme.store` |
| **App name** | Display name shown on the device home screen | `Acme` |
| **Shop domain** | Client's Shopify domain | `acme.myshopify.com` |
| **API key** | Shopify API key | `abc123...` |
| **Access token** | Shopify access token | `shpat_...` |
| **Preview visible** | Whether the preview menu item is shown | Toggle on/off |

### File uploads

| Upload | Required | Notes |
|---|---|---|
| **App icon** | Yes | PNG, 1024×1024 recommended. Automatically resized to all mipmap densities. |
| **Header logo** | Yes | PNG or JPG. Applied to all 4 screens by default. |
| **google-services.json** | No | Firebase config. If not uploaded, the base repo's default is used. |

**Per-screen logos:** Toggle "Different logo per screen?" to upload separate logos for the User Profile, Account Details, Login, and OTP screens.

### Submitting

Click **Create Client Project**. The status panel shows progress:

1. **Creating project…** — backend is cloning the base repo and applying changes
2. **Success** — the new GitHub repo URL is displayed; GitHub Actions has been triggered

The APK will be emailed to `NOTIFY_EMAIL` when the build completes (typically 5–15 minutes).

---

## What Gets Created

A new private GitHub repo named `{mid}_{project_name}` (e.g. `acme001_Acme_Store`) is created under `GITHUB_ORG` with:

- Package name changed throughout all Kotlin files, manifest, and build config
- App name updated in `strings.xml`
- App icon replaced at all mipmap densities (`ic_launcher.png`, `ic_launcher_round.png`)
- Header logo replaced in all 4 screen layouts
- `Urls.kt` updated with the shop domain, API key, access token, MID, and preview flag
- `google-services.json` replaced (if uploaded)
- GitHub Actions workflow included — triggers automatically on push to `main`

---

## After the Build

When GitHub Actions finishes:

- **Success:** You receive an email with a Google Drive link to download the APK
- **Failure:** You receive a failure notification email with a link to the Actions log

The APK is an unsigned release build (`app-release-unsigned.apk`). Sign it with your release keystore before distributing to users.

---

## Troubleshooting

**Form submits but status shows an error**

Check the backend terminal for the full error message. Common causes:
- `GITHUB_TOKEN` missing or lacks `repo` scope
- `BASE_ANDROID_REPO_URL` unreachable (check VPN, SSH keys, or HTTPS credentials)
- `BASE_PACKAGE_NAME` in `main.py` doesn't match the base repo's actual `applicationId`

**Package name validation error**

Package names must be at least 3 dot-separated lowercase segments, e.g. `com.client.app`. Single-word or two-segment names are rejected.

**GitHub Actions build fails**

Open the Actions tab on the new client repo to see the full log. Common causes:
- Missing secrets on the base repo (check all 5 are set)
- `gradlew` not executable — add `chmod +x gradlew` to the repo if needed
- Missing signing config — unsigned release builds may fail if `signingConfigs` is required in `build.gradle`

**APK email not received**

- Check the Actions log on the client repo for upload/email step errors
- Verify the service account has Editor access on the Drive folder
- Verify the Gmail app password is correct (not the account password)

---

## Stopping the Tool

Press `Ctrl+C` in each terminal window.

---

## Running Tests

### Backend

```bash
cd backend
python -m pytest tests/ -v
```

Expected: 45 tests pass across 6 modules (image_utils, asset_replacer, config_updater, github_api, package_renamer, main).

### Frontend (Playwright E2E)

The E2E tests start the Vite dev server automatically — no need to start it manually.

```bash
cd frontend
npx playwright test
```

Expected: 20 tests pass covering form rendering, toggles, file uploads, submit success/error states, and multipart field names.

To run with an interactive browser UI (useful for debugging):

```bash
cd frontend
npx playwright test --ui
```
