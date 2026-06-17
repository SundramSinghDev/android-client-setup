import os
import shutil
import tempfile
import pytest
from pathlib import Path
from PIL import Image


MIPMAP_FOLDERS = [
    "mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi",
    "mipmap-xxhdpi", "mipmap-xxxhdpi",
]


def _make_icon_source(path: str) -> None:
    Image.new("RGBA", (1024, 1024), (0, 128, 255, 255)).save(path)


def _make_mipmap_dirs(project_dir: str) -> None:
    res = Path(project_dir) / "app/src/main/res"
    for folder in MIPMAP_FOLDERS:
        d = res / folder
        d.mkdir(parents=True)
        Image.new("RGBA", (48, 48), (0, 0, 0, 255)).save(str(d / "ic_launcher.png"))
        Image.new("RGBA", (48, 48), (0, 0, 0, 255)).save(str(d / "ic_launcher_round.png"))


def _make_drawable_dir(project_dir: str, drawable_name: str = "header_logo") -> Path:
    d = Path(project_dir) / "app/src/main/res/drawable"
    d.mkdir(parents=True)
    Image.new("RGBA", (300, 100), (200, 200, 200, 255)).save(str(d / f"{drawable_name}.png"))
    return d


def test_google_services_json_replaced():
    from asset_replacer import replace_google_services
    with tempfile.TemporaryDirectory() as d:
        app_dir = Path(d) / "app"
        app_dir.mkdir()
        orig = app_dir / "google-services.json"
        orig.write_text('{"original": true}')

        new_gsj = os.path.join(d, "new.json")
        Path(new_gsj).write_text('{"client": true}')

        replace_google_services(d, new_gsj)
        assert '{"client": true}' == orig.read_text()


def test_google_services_json_skipped_when_none():
    from asset_replacer import replace_google_services
    with tempfile.TemporaryDirectory() as d:
        app_dir = Path(d) / "app"
        app_dir.mkdir()
        orig = app_dir / "google-services.json"
        orig.write_text('{"original": true}')

        replace_google_services(d, None)  # should be a no-op
        assert '{"original": true}' == orig.read_text()


def test_app_icon_placed_in_all_mipmap_folders():
    from asset_replacer import replace_app_icon
    with tempfile.TemporaryDirectory() as d:
        _make_mipmap_dirs(d)
        icon_src = os.path.join(d, "icon.png")
        _make_icon_source(icon_src)

        replace_app_icon(d, icon_src)

        res = Path(d) / "app/src/main/res"
        for folder in MIPMAP_FOLDERS:
            assert (res / folder / "ic_launcher.png").exists()
            assert (res / folder / "ic_launcher_round.png").exists()


def test_header_logo_replaced_single():
    from asset_replacer import replace_header_logo
    with tempfile.TemporaryDirectory() as d:
        drawable_dir = _make_drawable_dir(d, "header_logo")
        new_logo = os.path.join(d, "new_logo.png")
        Image.new("RGBA", (500, 200), (255, 0, 0, 255)).save(new_logo)

        replace_header_logo(d, new_logo)

        # Open and verify, then close properly
        replaced = Image.open(str(drawable_dir / "header_logo.png"))
        try:
            assert replaced.size == (500, 200)
        finally:
            replaced.close()


def test_header_logo_per_screen_override():
    from asset_replacer import replace_header_logo, SCREEN_LOGO_DRAWABLES
    with tempfile.TemporaryDirectory() as d:
        _make_drawable_dir(d, "header_logo")
        default_logo = os.path.join(d, "default.png")
        login_logo = os.path.join(d, "login_logo.png")
        Image.new("RGBA", (300, 100), (0, 255, 0, 255)).save(default_logo)
        Image.new("RGBA", (400, 150), (0, 0, 255, 255)).save(login_logo)

        replace_header_logo(d, default_logo, per_screen={"login": login_logo})

        drawable_dir = Path(d) / "app/src/main/res/drawable"
        login_drawable = SCREEN_LOGO_DRAWABLES["login"]
        replaced = Image.open(str(drawable_dir / f"{login_drawable}.png"))
        try:
            assert replaced.size == (400, 150)
        finally:
            replaced.close()
