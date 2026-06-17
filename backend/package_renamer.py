import os
import shutil
from pathlib import Path


def rename_package(project_dir: str, old_package: str, new_package: str) -> None:
    """
    Rename Android package throughout the project.
    Updates .kt files, AndroidManifest.xml, app/build.gradle,
    and renames the source directory tree.
    """
    root = Path(project_dir)
    src_main = root / "app" / "src" / "main"
    java_root = next(
        (src_main / d for d in ("java", "kotlin") if (src_main / d).exists()),
        None,
    )
    if java_root is None:
        raise FileNotFoundError(
            f"Source directory not found: expected 'java' or 'kotlin' under {src_main}"
        )

    # 1. Replace string in all .kt files
    for kt_file in java_root.rglob("*.kt"):
        _replace_in_file(kt_file, old_package, new_package)

    # 2. Replace in AndroidManifest.xml
    manifest = root / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest.exists():
        _replace_in_file(manifest, old_package, new_package)

    # 3. Replace applicationId in build.gradle (Groovy or KTS)
    for gradle_name in ("build.gradle", "build.gradle.kts"):
        gradle = root / "app" / gradle_name
        if gradle.exists():
            _replace_in_file(gradle, old_package, new_package)
            break

    # 4. Rename directory structure
    old_dir = java_root / Path(*old_package.split("."))
    new_dir = java_root / Path(*new_package.split("."))
    if old_dir.exists() and old_dir != new_dir:
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(old_dir), str(new_dir), dirs_exist_ok=True)
        shutil.rmtree(str(old_dir))
        _remove_empty_parents(old_dir.parent, java_root)


def _replace_in_file(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")


def _remove_empty_parents(directory: Path, stop_at: Path) -> None:
    """Walk up and remove empty directories until stop_at."""
    current = directory
    while current != stop_at:
        try:
            current.rmdir()  # Only removes if empty
        except OSError:
            break
        current = current.parent
