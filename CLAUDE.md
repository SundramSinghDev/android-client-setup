# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Purpose

This project automates the creation of new Android client projects — it takes client-specific config (package name, app name, API credentials, logo assets) via a web form and produces a ready-to-build GitHub repo with all substitutions applied and a GitHub Actions CI workflow that builds the APK and emails it when done.

## Architecture

Three layers:
1. **Frontend** (`frontend/`) — React (Vite) web form that collects client config and file uploads, then POSTs to the backend.
2. **Backend** (`backend/`) — Python FastAPI server that clones the base Android repo, applies all substitutions (package rename, string config, assets), creates a new GitHub repo, and pushes the result.
3. **CI/CD** (`.github/`) — GitHub Actions workflow (`build.yml`) on the generated repo that builds the APK and uploads it; `upload_and_notify.py` handles Drive upload and email notification.

## Commands

**Backend**
```bash
cd backend
pip install -r requirements.txt       # install deps
uvicorn main:app --reload --port 8000  # start server
python -m pytest tests/ -v            # run all tests
python -m pytest tests/test_foo.py::test_name -v  # run one test
```

**Frontend**
```bash
cd frontend
npm install                # install deps
npm run dev                # start dev server at localhost:5173
npx playwright test        # run E2E tests (starts dev server automatically)
npx playwright test --ui   # run E2E tests with interactive UI
```

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

## Running Tests

**Backend**
```bash
cd backend
python -m pytest tests/ -v
```

Expected: 45 tests pass (3 image_utils, 5 asset_replacer, 4 config_updater, 7 github_api, 5 package_renamer, 21 main).

**Frontend (Playwright E2E)**
```bash
cd frontend
npx playwright test
```

Expected: 20 tests pass (5 page structure, 3 preview toggle, 3 per-screen toggle, 6 submit success, 3 submit error, 1 per-screen submission).

## Key Constants

These must be updated to match the base Android repo before first use:

- `BASE_PACKAGE_NAME = "com.example.baseapp"` — in `backend/main.py`; must match the `applicationId` in the base repo's `app/build.gradle`.
- `HEADER_LOGO_DRAWABLE_NAME = "header_logo"` — in `backend/asset_replacer.py`; must match the drawable name referenced in the 4 layout files.
- `SCREEN_LOGO_DRAWABLES` — in `backend/asset_replacer.py`; maps screen keys to drawable names:
  ```python
  SCREEN_LOGO_DRAWABLES = {
      "userprofile":     "header_logo",
      "account_details": "header_logo",
      "login":           "header_logo",
      "otp":             "header_logo",
  }
  ```
- `ICON_SIZES` — in `backend/image_utils.py`; Android mipmap densities (do not change unless Android changes):
  ```python
  ICON_SIZES = {
      "mipmap-mdpi":    48,
      "mipmap-hdpi":    72,
      "mipmap-xhdpi":   96,
      "mipmap-xxhdpi":  144,
      "mipmap-xxxhdpi": 192,
  }
  ```

## Environment Variables

Copy `.env.example` to `.env` and fill in the values before starting the backend:

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | Personal access token with `repo` scope (to create repos and push) |
| `GITHUB_ORG` | GitHub organisation or username under which new repos are created |
| `BASE_ANDROID_REPO_URL` | HTTPS URL of the base Android repo to clone (e.g. `https://github.com/yourorg/base-android.git`) |

## Module Overview

| Module | Description |
|---|---|
| `main.py` | FastAPI app with `/health` and `/api/create-client` endpoints; orchestrates the full pipeline |
| `image_utils.py` | Resizes a source PNG to all Android mipmap densities using Pillow |
| `asset_replacer.py` | Copies app icon (all densities), header logo(s), and google-services.json into the project tree |
| `package_renamer.py` | Renames Android package in .kt files, AndroidManifest.xml, build.gradle, and directory structure |
| `config_updater.py` | Updates `app_name` in strings.xml and all config values + preview flag in Urls.kt |
| `github_api.py` | Clones the base repo, creates a new private GitHub repo, and pushes the customised project |

## Architecture Reference

See `docs/superpowers/specs/2026-06-16-client-project-automation-design.md` for the full design spec.

## First-Run E2E Verification

After setting up all credentials in `.env`:

1. Start the backend: `cd backend && uvicorn main:app --reload --port 8000`
2. Start the frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173`, fill in all fields with test values, upload a test PNG icon and logo, and submit.
4. Expected sequence:
   - Status panel shows "Creating project…"
   - Backend logs show: clone → substitutions → GitHub push
   - Status panel shows success with repo URL
   - New GitHub repo exists at `https://github.com/{GITHUB_ORG}/{mid}_{project_name}`
   - GitHub Actions workflow starts, builds APK, uploads to Drive, emails link
