from pathlib import Path


def find_module_dir(project_dir: str | Path) -> Path:
    """
    Auto-detect the Android module directory (e.g. 'app', 'base') by finding
    the first direct subdirectory that contains src/main/.
    """
    root = Path(project_dir)
    for candidate in sorted(root.iterdir()):
        if candidate.is_dir() and (candidate / "src" / "main").exists():
            return candidate
    raise FileNotFoundError(
        f"No Android module directory found in {root}. "
        f"Expected a subdirectory containing src/main/."
    )
