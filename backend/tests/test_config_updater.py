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


def _make_config_files(project_dir: str, preview_visible: bool = True) -> None:
    """Create utils/Urls.kt and LeftMenu.kt matching the actual base repo structure."""
    pkg = Path(project_dir) / "app/src/main/java/com/example/app/utils"
    pkg.mkdir(parents=True)
    (pkg / "Urls.kt").write_text(
        'package com.example.app.utils\n\n'
        'class Urls {\n'
        '    val mid: String\n'
        '        get() {\n'
        '            var domain = "OLD_MID"\n'
        '            return domain\n'
        '        }\n'
        '    val shopdomain: String\n'
        '        get() {\n'
        '            var domain = "old.myshopify.com"\n'
        '            return domain\n'
        '        }\n'
        '    val apikey: String\n'
        '        get() {\n'
        '            var key = "OLD_KEY"\n'
        '            return key\n'
        '        }\n'
        '    val accessToken: String = BuildConfig.SHOP_ACCESS_TOKEN\n'
        '}\n'
    )

    visibility = "View.VISIBLE" if preview_visible else "View.GONE"
    fragments = Path(project_dir) / "app/src/main/java/com/example/app/fragments"
    fragments.mkdir(parents=True)
    (fragments / "LeftMenu.kt").write_text(
        'package com.example.app.fragments\n\n'
        'class LeftMenu {\n'
        '    fun onResume() {\n'
        '        when (requireActivity().packageName) {\n'
        '            "com.magenative.app" -> {\n'
        f'                menuData!!.previewvislible = {visibility}\n'
        '            }\n'
        '            else -> {\n'
        '                menuData!!.previewvislible = View.GONE\n'
        '            }\n'
        '        }\n'
        '    }\n'
        '}\n'
    )


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
        _make_config_files(d)
        update_urls_kt(d, "MID123", "new.myshopify.com", "KEY456", "TOKEN789", True)
        content = (Path(d) / "app/src/main/java/com/example/app/utils/Urls.kt").read_text()
        assert '"MID123"' in content
        assert '"new.myshopify.com"' in content
        assert '"KEY456"' in content
        assert '"TOKEN789"' in content
        assert "OLD_MID" not in content
        assert "OLD_KEY" not in content
        assert "BuildConfig" not in content


def test_preview_set_to_gone():
    from config_updater import update_urls_kt
    with tempfile.TemporaryDirectory() as d:
        _make_config_files(d, preview_visible=True)
        update_urls_kt(d, "M", "s.myshopify.com", "K", "T", preview_visible=False)
        content = (Path(d) / "app/src/main/java/com/example/app/fragments/LeftMenu.kt").read_text()
        assert "View.GONE" in content
        assert "View.VISIBLE" not in content


def test_preview_set_to_visible():
    from config_updater import update_urls_kt
    with tempfile.TemporaryDirectory() as d:
        _make_config_files(d, preview_visible=False)
        update_urls_kt(d, "M", "s.myshopify.com", "K", "T", preview_visible=True)
        content = (Path(d) / "app/src/main/java/com/example/app/fragments/LeftMenu.kt").read_text()
        assert "View.VISIBLE" in content
        assert "View.GONE" not in content
