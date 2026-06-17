import shutil
from pathlib import Path
from image_utils import resize_icon_to_all_densities

# Drawable resource name used for the header logo in the base repo.
# Verify this against the 4 layout files before first use:
#   m_userprofile.xml, activity_customer_account_details.xml,
#   m_login_page.xml, activity_otp_verification.xml
HEADER_LOGO_DRAWABLE_NAME = "header_logo"

# Maps per-screen keys to their drawable resource names.
# Update these values if each screen uses a different drawable name.
SCREEN_LOGO_DRAWABLES = {
    "userprofile":     HEADER_LOGO_DRAWABLE_NAME,
    "account_details": HEADER_LOGO_DRAWABLE_NAME,
    "login":           HEADER_LOGO_DRAWABLE_NAME,
    "otp":             HEADER_LOGO_DRAWABLE_NAME,
}


def replace_google_services(project_dir: str, gsj_source: str | None) -> None:
    """Overwrite app/google-services.json if a replacement is provided."""
    if gsj_source is None:
        return
    dest = Path(project_dir) / "app" / "google-services.json"
    shutil.copy2(gsj_source, dest)


def replace_app_icon(project_dir: str, icon_source: str) -> None:
    """Resize icon and overwrite ic_launcher / ic_launcher_round in all mipmap-* folders."""
    res_dir = Path(project_dir) / "app" / "src" / "main" / "res"
    sized = resize_icon_to_all_densities(icon_source)
    for folder_name, (launcher_img, round_img) in sized.items():
        folder = res_dir / folder_name
        if folder.exists():
            launcher_img.save(str(folder / "ic_launcher.png"))
            round_img.save(str(folder / "ic_launcher_round.png"))


def replace_header_logo(
    project_dir: str,
    logo_source: str,
    per_screen: dict | None = None,
) -> None:
    """
    Replace header logo drawable(s).

    per_screen: optional dict mapping screen key -> local file path.
    Valid keys: "userprofile", "account_details", "login", "otp".
    If None, logo_source is used for all screens (overwrites one shared file).
    """
    drawable_dir = Path(project_dir) / "app" / "src" / "main" / "res" / "drawable"

    if per_screen:
        for screen_key, logo_path in per_screen.items():
            drawable_name = SCREEN_LOGO_DRAWABLES.get(screen_key, HEADER_LOGO_DRAWABLE_NAME)
            _copy_logo(logo_path, drawable_dir, drawable_name)
        # Write the default logo for any screens not overridden
        overridden_drawables = {
            SCREEN_LOGO_DRAWABLES[k] for k in per_screen if k in SCREEN_LOGO_DRAWABLES
        }
        if HEADER_LOGO_DRAWABLE_NAME not in overridden_drawables:
            _copy_logo(logo_source, drawable_dir, HEADER_LOGO_DRAWABLE_NAME)
    else:
        _copy_logo(logo_source, drawable_dir, HEADER_LOGO_DRAWABLE_NAME)


def _copy_logo(source: str, drawable_dir: Path, drawable_name: str) -> None:
    suffix = Path(source).suffix or ".png"
    shutil.copy2(source, drawable_dir / f"{drawable_name}{suffix}")
