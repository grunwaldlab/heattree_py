#!/usr/bin/env python3
"""Download the heat-tree JavaScript library from unpkg.

This script downloads the minified IIFE build of @grunwaldlab/heat-tree
and saves it to src/heattree_py/_static/ for offline embedding.
"""

import re
import urllib.request
from pathlib import Path


def _get_version_from_source():
    """Read HEAT_TREE_JS_VERSION from __init__.py without importing."""
    init_file = Path(__file__).parent.parent / "src" / "heattree_py" / "__init__.py"
    content = init_file.read_text()
    match = re.search(r'HEAT_TREE_JS_VERSION\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find HEAT_TREE_JS_VERSION in __init__.py")


STATIC_DIR = Path(__file__).parent.parent / "src" / "heattree_py" / "_static"
JS_FILENAME = "heat-tree.iife.min.js"

# Get version from source file (not import, for build compatibility)
HEAT_TREE_JS_VERSION = _get_version_from_source()

CDN_URL = (
    f"https://unpkg.com/@grunwaldlab/heat-tree@{HEAT_TREE_JS_VERSION}/dist/{JS_FILENAME}"
)


def download_js():
    """Download the heat-tree JS from unpkg."""
    output_path = STATIC_DIR / JS_FILENAME

    print(f"Downloading heat-tree v{HEAT_TREE_JS_VERSION}...")
    print(f"URL: {CDN_URL}")
    print(f"Output: {output_path}")

    try:
        urllib.request.urlretrieve(CDN_URL, output_path)
        size = output_path.stat().st_size
        print(f"Success! Downloaded {size:,} bytes")
        return 0
    except Exception as e:
        print(f"Error downloading: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(download_js())
