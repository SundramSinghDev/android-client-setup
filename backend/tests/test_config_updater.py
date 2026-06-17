import tempfile
import pytest
from pathlib import Path


def _make_strings_xml(project_dir: str, app_name: str) -> None:
    res = Path(project_dir) / "app/src/main/res/values"
    res.mkdir(parents=True)
    (res / "strings.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<resources>\n'
        f'    <string name="app_name">{app_name}</string>\n'
        '</resources>'
    )


def _make_urls_kt(project_dir: str, visible: bool = True) -> Path:
    pkg = Path(project_dir) / "app/src/main/java/com/example/app"
    pkg.mkdir(parents=True)
    visibility = "View.VISIBLE" if visible else "View.GONE"
    (pkg / "Urls.kt").write_text(
        'object Urls {\n'
        '    val mid = "OLD_MID"\n'
        '    val shopdomain = "old.myshopify.com"\n'
        '    val apikey = "OLD_KEY"\n'
        '    val accessToken = "OLD_TOKEN"\n'
        '}\n'
        '\n'
        'fun setup() {\n'
        f'    menuData!!.previewvislible = {visibility}\n'
        '}\n'
    )
    return pkg / "Urls.kt"


def test_app_name_updated():
    from config_updater import update_app_name
    with tempfile.TemporaryDirectory() as d:
        _make_strings_xml(d, "Old App")
        update_app_name(d, "New Client")
        content = (Path(d) / "app/src/main/res/values/strings.xml").read_text()
        assert "New Client" in content
        assert "Old App" not in content


def test_urls_kt_values_updated():
    from config_updater import update_urls_kt
    with tempfile.TemporaryDirectory() as d:
        _make_urls_kt(d)
        update_urls_kt(d, "MID123", "new.myshopify.com", "KEY456", "TOKEN789", True)
        content = (Path(d) / "app/src/main/java/com/example/app/Urls.kt").read_text()
        assert '"MID123"' in content
        assert '"new.myshopify.com"' in content
        assert '"KEY456"' in content
        assert '"TOKEN789"' in content


def test_preview_set_to_gone():
    from config_updater import update_urls_kt
    with tempfile.TemporaryDirectory() as d:
        _make_urls_kt(d, visible=True)
        update_urls_kt(d, "M", "s.myshopify.com", "K", "T", preview_visible=False)
        content = (Path(d) / "app/src/main/java/com/example/app/Urls.kt").read_text()
        assert "View.GONE" in content
        assert "View.VISIBLE" not in content


def test_preview_set_to_visible():
    from config_updater import update_urls_kt
    with tempfile.TemporaryDirectory() as d:
        _make_urls_kt(d, visible=False)
        update_urls_kt(d, "M", "s.myshopify.com", "K", "T", preview_visible=True)
        content = (Path(d) / "app/src/main/java/com/example/app/Urls.kt").read_text()
        assert "View.VISIBLE" in content
        assert "View.GONE" not in content
