import asyncio
import json
import os
import re as _re
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from asset_replacer import replace_app_icon, replace_google_services, replace_header_logo
from config_updater import update_app_name, update_urls_kt
from github_api import clone_base_repo, create_github_repo, push_to_github
from package_renamer import rename_package

load_dotenv()

BASE_ANDROID_REPO_URL = os.getenv("BASE_ANDROID_REPO_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG")

# ── Update this to match the applicationId in your base repo's app/build.gradle ──
BASE_PACKAGE_NAME = "com.example.baseapp"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/create-client")
async def create_client(
    project_name: str = Form(...),
    mid: str = Form(...),
    package_name: str = Form(...),
    app_name: str = Form(...),
    shop_domain: str = Form(...),
    api_key: str = Form(...),
    access_token: str = Form(...),
    preview_visible: bool = Form(True),
    app_icon: UploadFile = File(...),
    header_logo: UploadFile = File(...),
    google_services_json: UploadFile | None = File(None),
    logo_userprofile: UploadFile | None = File(None),
    logo_account_details: UploadFile | None = File(None),
    logo_login: UploadFile | None = File(None),
    logo_otp: UploadFile | None = File(None),
):
    if not _re.match(r'^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*){2,}$', package_name):
        raise HTTPException(status_code=422, detail="Invalid package_name: must be like com.example.app")

    raw_name = f"{mid}_{project_name}".replace(' ', '_')
    repo_name = _re.sub(r'[^a-zA-Z0-9._-]', '-', raw_name)

    work_dir = tempfile.mkdtemp(prefix="client_setup_")
    assets_dir = os.path.join(work_dir, "assets")
    os.makedirs(assets_dir)

    # Save uploads to disk before streaming starts
    icon_path = await _save_upload(app_icon, assets_dir, "icon")
    logo_path = await _save_upload(header_logo, assets_dir, "header_logo")
    gsj_path = (
        await _save_upload(google_services_json, assets_dir, "google-services")
        if google_services_json and google_services_json.filename
        else None
    )
    per_screen = {}
    for key, upload in [
        ("userprofile", logo_userprofile),
        ("account_details", logo_account_details),
        ("login", logo_login),
        ("otp", logo_otp),
    ]:
        if upload and upload.filename:
            per_screen[key] = await _save_upload(upload, assets_dir, f"logo_{key}")

    async def generate():
        project_dir = os.path.join(work_dir, "project")
        try:
            yield _sse({"step": "Cloning base repository…"})
            await asyncio.to_thread(clone_base_repo, BASE_ANDROID_REPO_URL, project_dir, GITHUB_TOKEN)

            yield _sse({"step": "Renaming package…"})
            await asyncio.to_thread(rename_package, project_dir, BASE_PACKAGE_NAME, package_name)

            yield _sse({"step": "Updating app configuration…"})
            await asyncio.to_thread(update_app_name, project_dir, app_name)
            await asyncio.to_thread(update_urls_kt, project_dir, mid, shop_domain, api_key, access_token, preview_visible)

            yield _sse({"step": "Replacing assets…"})
            await asyncio.to_thread(replace_google_services, project_dir, gsj_path)
            await asyncio.to_thread(replace_app_icon, project_dir, icon_path)
            await asyncio.to_thread(replace_header_logo, project_dir, logo_path, per_screen or None)

            yield _sse({"step": "Creating GitHub repository…"})
            repo_url = await asyncio.to_thread(create_github_repo, GITHUB_TOKEN, GITHUB_ORG, repo_name)

            yield _sse({"step": "Pushing to GitHub…"})
            await asyncio.to_thread(push_to_github, project_dir, repo_url, GITHUB_TOKEN)

            yield _sse({
                "status": "build_triggered",
                "repo_url": repo_url,
                "message": "Project created. Build triggered — APK will be emailed when ready.",
            })
        except Exception as exc:
            yield _sse({"status": "error", "message": str(exc)})
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _save_upload(upload: UploadFile, dest_dir: str, name: str) -> str:
    suffix = Path(upload.filename).suffix or ".bin"
    dest = os.path.join(dest_dir, f"{name}{suffix}")
    with open(dest, "wb") as f:
        f.write(await upload.read())
    return dest
