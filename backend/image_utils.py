from PIL import Image

ICON_SIZES = {
    "mipmap-mdpi":    48,
    "mipmap-hdpi":    72,
    "mipmap-xhdpi":   96,
    "mipmap-xxhdpi":  144,
    "mipmap-xxxhdpi": 192,
}


def resize_icon_to_all_densities(source_path: str) -> dict:
    """
    Resize a source image to all Android mipmap densities.

    Returns dict of {folder_name: (launcher_img, round_img)}
    where each value is a tuple of PIL Image objects (RGBA).
    """
    source = Image.open(source_path).convert("RGBA")
    result = {}
    for folder_name, size in ICON_SIZES.items():
        resized = source.resize((size, size), Image.LANCZOS)
        result[folder_name] = (resized, resized.copy())
    return result
