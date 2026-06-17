# .github/scripts/upload_and_notify.py
import argparse
import json
import os
import smtplib
from email.mime.text import MIMEText

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def upload_to_drive(apk_path: str, folder_id: str, sa_json: str) -> str:
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_json),
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    service = build("drive", "v3", credentials=credentials)
    file_meta = {"name": os.path.basename(apk_path), "parents": [folder_id]}
    media = MediaFileUpload(apk_path, mimetype="application/vnd.android.package-archive")
    file = service.files().create(body=file_meta, media_body=media, fields="id").execute()
    service.permissions().create(
        fileId=file["id"], body={"type": "anyone", "role": "reader"}
    ).execute()
    return f"https://drive.google.com/file/d/{file['id']}/view?usp=sharing"


def send_email(to: str, user: str, password: str, link: str, repo: str) -> None:
    msg = MIMEText(
        f"APK build complete for {repo}.\n\nDownload: {link}\n\n(Publicly accessible link)"
    )
    msg["Subject"] = f"APK Ready: {repo}"
    msg["From"] = user
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def send_failure_email(to: str, user: str, password: str, repo: str, run_url: str) -> None:
    msg = MIMEText(
        f"The release build failed. Check the Actions log at {run_url}"
    )
    msg["Subject"] = f"Build failed: {repo}"
    msg["From"] = user
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--failure", action="store_true", help="Send failure notification email only")
    args = parser.parse_args()

    if args.failure:
        repo = os.environ["REPO_NAME"]
        run_url = os.environ["RUN_URL"]
        send_failure_email(
            os.environ["NOTIFY_EMAIL"],
            os.environ["GMAIL_USER"],
            os.environ["GMAIL_APP_PASSWORD"],
            repo,
            run_url,
        )
        print("Failure email sent.")
    else:
        apk = os.environ["APK_PATH"]
        link = upload_to_drive(
            apk, os.environ["GOOGLE_DRIVE_FOLDER_ID"], os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
        )
        print(f"Uploaded: {link}")
        send_email(
            os.environ["NOTIFY_EMAIL"],
            os.environ["GMAIL_USER"],
            os.environ["GMAIL_APP_PASSWORD"],
            link,
            os.environ["REPO_NAME"],
        )
        print("Email sent.")
