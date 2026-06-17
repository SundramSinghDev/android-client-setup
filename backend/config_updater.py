import html
import re
from pathlib import Path
from project_utils import find_module_dir


def update_app_name(project_dir: str, app_name: str) -> None:
    """Replace app_name value in res/values/strings.xml."""
    module_dir = find_module_dir(project_dir)
    strings_xml = module_dir / "src" / "main" / "res" / "values" / "strings.xml"
    content = strings_xml.read_text(encoding="utf-8")
    escaped = html.escape(app_name)
    updated, count = re.subn(
        r'(<string name="app_name">)[^<]*(</string>)',
        lambda m: m.group(1) + escaped + m.group(2),
        content,
    )
    if count == 0:
        raise ValueError(f"'app_name' string not found in {strings_xml}")
    strings_xml.write_text(updated, encoding="utf-8")


def update_urls_kt(
    project_dir: str,
    mid: str,
    shop_domain: str,
    api_key: str,
    access_token: str,
    preview_visible: bool,
) -> None:
    """Update config values in utils/Urls.kt and preview toggle in LeftMenu.kt."""
    project_path = Path(project_dir)

    # --- Urls.kt: mid, shopdomain, apikey, accessToken ---
    urls_kt = _find_urls_kt(project_path)
    content = urls_kt.read_text(encoding="utf-8")

    content = _replace_getter_value(content, "mid", "domain", mid)
    content = _replace_getter_value(content, "shopdomain", "domain", shop_domain)
    content = _replace_getter_value(content, "apikey", "key", api_key)

    # accessToken is assigned from BuildConfig — replace with a string literal
    content, count = re.subn(
        r'(val accessToken: String\s*=\s*)BuildConfig\.\w+',
        lambda m: m.group(1) + f'"{access_token}"',
        content,
    )
    if count == 0:
        raise ValueError("accessToken not found in Urls.kt")

    urls_kt.write_text(content, encoding="utf-8")

    # --- LeftMenu.kt: preview visibility ---
    left_menu_kt = _find_left_menu_kt(project_path)
    lm_content = left_menu_kt.read_text(encoding="utf-8")
    preview_val = "View.VISIBLE" if preview_visible else "View.GONE"

    # Replace the when(packageName) block with a direct assignment
    lm_content, count = re.subn(
        r'when\s*\(requireActivity\(\)\.packageName\)\s*\{'
        r'.*?"com\.magenative\.app"\s*->\s*\{[^}]*\}'
        r'.*?else\s*->\s*\{[^}]*\}'
        r'\s*\}',
        f'menuData!!.previewvislible = {preview_val}',
        lm_content,
        flags=re.DOTALL,
    )
    if count == 0:
        raise ValueError("Preview visibility when-block not found in LeftMenu.kt")
    left_menu_kt.write_text(lm_content, encoding="utf-8")


def _replace_getter_value(content: str, getter_name: str, var_name: str, new_value: str) -> str:
    """Replace the first var assignment inside a named property getter."""
    getter_pos = content.find(f'val {getter_name}:')
    if getter_pos == -1:
        raise ValueError(f"Getter '{getter_name}' not found in Urls.kt")
    tail = content[getter_pos:]
    new_tail, count = re.subn(
        rf'(var {var_name}\s*=\s*")[^"]*(")',
        lambda m: m.group(1) + new_value + m.group(2),
        tail,
        count=1,
    )
    if count == 0:
        raise ValueError(f"Variable '{var_name}' not found in getter '{getter_name}'")
    return content[:getter_pos] + new_tail


def _find_urls_kt(project_path: Path) -> Path:
    module_dir = find_module_dir(project_path)
    for f in (module_dir / "src").rglob("Urls.kt"):
        if "productsection" not in f.parts:
            return f
    raise FileNotFoundError(f"utils Urls.kt not found under {module_dir}/src/")


def _find_left_menu_kt(project_path: Path) -> Path:
    module_dir = find_module_dir(project_path)
    for f in (module_dir / "src").rglob("LeftMenu.kt"):
        return f
    raise FileNotFoundError(f"LeftMenu.kt not found under {module_dir}/src/")
