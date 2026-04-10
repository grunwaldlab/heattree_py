"""Static assets bundled with the package."""

from pathlib import Path

_STATIC_DIR = Path(__file__).parent

def get_js_path():
    """Return the path to the bundled heat-tree JS file."""
    return _STATIC_DIR / "heat-tree.iife.min.js"

def get_js_content():
    """Return the contents of the bundled heat-tree JS file."""
    path = get_js_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Bundled JS not found at {path}. "
            "Run 'hatch run update-js' to download it."
        )
    return path.read_text()
