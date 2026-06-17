import re
from pathlib import Path


def update_app_name(project_dir: str, app_name: str) -> None:
    """Replace app_name value in res/values/strings.xml."""
    strings_xml = (
        Path(project_dir) / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    )
    content = strings_xml.read_text(encoding="utf-8")
    updated = re.sub(
        r'(<string name="app_name">)[^<]*(</string>)',
        rf'\g<1>{app_name}\g<2>',
        content,
    )
    strings_xml.write_text(updated, encoding="utf-8")


def update_urls_kt(
    project_dir: str,
    mid: str,
    shop_domain: str,
    api_key: str,
    access_token: str,
    preview_visible: bool,
) -> None:
    """Update all config values and the preview visibility flag in Urls.kt."""
    urls_kt = _find_urls_kt(Path(project_dir))
    content = urls_kt.read_text(encoding="utf-8")

    replacements = {
        r'(val mid\s*=\s*")[^"]*(")'         : rf'\g<1>{mid}\g<2>',
        r'(val shopdomain\s*=\s*")[^"]*(")'   : rf'\g<1>{shop_domain}\g<2>',
        r'(val apikey\s*=\s*")[^"]*(")'       : rf'\g<1>{api_key}\g<2>',
        r'(val accessToken\s*=\s*")[^"]*(")'  : rf'\g<1>{access_token}\g<2>',
    }
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)

    if preview_visible:
        content = content.replace(
            "menuData!!.previewvislible = View.GONE",
            "menuData!!.previewvislible = View.VISIBLE",
        )
    else:
        content = content.replace(
            "menuData!!.previewvislible = View.VISIBLE",
            "menuData!!.previewvislible = View.GONE",
        )

    urls_kt.write_text(content, encoding="utf-8")


def _find_urls_kt(project_path: Path) -> Path:
    for f in (project_path / "app" / "src").rglob("Urls.kt"):
        return f
    raise FileNotFoundError("Urls.kt not found under app/src/")
