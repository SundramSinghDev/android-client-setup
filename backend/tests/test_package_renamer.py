import os
import tempfile
import pytest
from pathlib import Path


def _make_android_project(base: str, package: str) -> None:
    """Create a minimal Android project tree for testing."""
    pkg_path = Path(base) / "app/src/main/java" / Path(*package.split("."))
    pkg_path.mkdir(parents=True)
    (pkg_path / "MainActivity.kt").write_text(
        f"package {package}\n\nimport {package}.utils.Foo\n\nclass MainActivity"
    )
    manifest = Path(base) / "app/src/main/AndroidManifest.xml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(f'<manifest package="{package}" xmlns:android="http://schemas.android.com/apk/res/android">')
    build = Path(base) / "app/build.gradle"
    build.parent.mkdir(parents=True, exist_ok=True)
    build.write_text(f'android {{\n    defaultConfig {{\n        applicationId "{package}"\n    }}\n}}')


def test_kt_files_have_new_package():
    from package_renamer import rename_package
    with tempfile.TemporaryDirectory() as d:
        _make_android_project(d, "com.example.old")
        rename_package(d, "com.example.old", "com.newclient.app")
        kt = Path(d) / "app/src/main/java/com/newclient/app/MainActivity.kt"
        content = kt.read_text()
        assert "package com.newclient.app" in content
        assert "com.example.old" not in content


def test_manifest_has_new_package():
    from package_renamer import rename_package
    with tempfile.TemporaryDirectory() as d:
        _make_android_project(d, "com.example.old")
        rename_package(d, "com.example.old", "com.newclient.app")
        content = (Path(d) / "app/src/main/AndroidManifest.xml").read_text()
        assert 'package="com.newclient.app"' in content
        assert "com.example.old" not in content


def test_build_gradle_has_new_application_id():
    from package_renamer import rename_package
    with tempfile.TemporaryDirectory() as d:
        _make_android_project(d, "com.example.old")
        rename_package(d, "com.example.old", "com.newclient.app")
        content = (Path(d) / "app/build.gradle").read_text()
        assert '"com.newclient.app"' in content
        assert "com.example.old" not in content


def test_directory_structure_renamed():
    from package_renamer import rename_package
    with tempfile.TemporaryDirectory() as d:
        _make_android_project(d, "com.example.old")
        rename_package(d, "com.example.old", "com.newclient.app")
        assert (Path(d) / "app/src/main/java/com/newclient/app").exists()
        assert not (Path(d) / "app/src/main/java/com/example/old").exists()


def test_works_with_kotlin_source_dir():
    from package_renamer import rename_package
    with tempfile.TemporaryDirectory() as d:
        # Use kotlin/ instead of java/
        pkg_path = Path(d) / "app/src/main/kotlin/com/example/old"
        pkg_path.mkdir(parents=True)
        (pkg_path / "MainActivity.kt").write_text("package com.example.old\n")
        (Path(d) / "app/src/main/AndroidManifest.xml").parent.mkdir(parents=True, exist_ok=True)
        (Path(d) / "app/src/main/AndroidManifest.xml").write_text('<manifest package="com.example.old">')
        (Path(d) / "app/build.gradle").parent.mkdir(parents=True, exist_ok=True)
        (Path(d) / "app/build.gradle").write_text('applicationId "com.example.old"')
        rename_package(d, "com.example.old", "com.newclient.app")
        kt = Path(d) / "app/src/main/kotlin/com/newclient/app/MainActivity.kt"
        assert kt.exists()
        assert "com.newclient.app" in kt.read_text()


def test_raises_when_java_root_missing():
    from package_renamer import rename_package
    with tempfile.TemporaryDirectory() as d:
        # No java directory — just an empty project root
        with pytest.raises(FileNotFoundError, match="Source directory not found"):
            rename_package(d, "com.example.old", "com.newclient.app")
