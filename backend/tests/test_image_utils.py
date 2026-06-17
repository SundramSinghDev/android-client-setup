import os
import tempfile
import pytest
from PIL import Image


def make_png(path: str, w: int = 1024, h: int = 1024) -> None:
    Image.new("RGBA", (w, h), (255, 0, 0, 255)).save(path)


def test_returns_all_density_folders():
    from image_utils import resize_icon_to_all_densities, ICON_SIZES
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "icon.png")
        make_png(src)
        result = resize_icon_to_all_densities(src)
        assert set(result.keys()) == set(ICON_SIZES.keys())


def test_each_density_has_correct_size():
    from image_utils import resize_icon_to_all_densities, ICON_SIZES
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "icon.png")
        make_png(src)
        result = resize_icon_to_all_densities(src)
        for folder, size in ICON_SIZES.items():
            launcher, round_icon = result[folder]
            assert launcher.size == (size, size), f"{folder} launcher wrong size"
            assert round_icon.size == (size, size), f"{folder} round wrong size"
            assert launcher.mode == "RGBA", f"{folder} launcher not RGBA"
            assert round_icon.mode == "RGBA", f"{folder} round not RGBA"


def test_non_square_source_still_produces_correct_sizes():
    from image_utils import resize_icon_to_all_densities, ICON_SIZES
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "icon.png")
        make_png(src, 800, 600)
        result = resize_icon_to_all_densities(src)
        for folder, size in ICON_SIZES.items():
            launcher, _ = result[folder]
            assert launcher.size == (size, size)
