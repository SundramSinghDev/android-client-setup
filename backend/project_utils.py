from pathlib import Path

# Name of the Android app module in the base repo.
# Update this if the module is not named "base".
ANDROID_MODULE_NAME = "base"


def find_module_dir(project_dir: str | Path) -> Path:
    """
    Return the Android app module directory.
    Tries ANDROID_MODULE_NAME first, then falls back to scanning for any
    direct subdirectory that contains src/main/.
    """
    root = Path(project_dir)
    preferred = root / ANDROID_MODULE_NAME
    if preferred.is_dir() and (preferred / "src" / "main").exists():
        return preferred
    for candidate in sorted(root.iterdir()):
        if candidate.is_dir() and (candidate / "src" / "main").exists():
            return candidate
    raise FileNotFoundError(
        f"No Android module directory found in {root}. "
        f"Expected a subdirectory containing src/main/."
    )
