"""Hatch build hook to ensure JS is bundled before building."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build hook that downloads JS if not present."""

    def initialize(self, version, build_data):
        """Initialize the build hook.

        Called before the build starts. Downloads the heat-tree JS
        if it's not already present in the static directory.
        """
        static_dir = Path(self.root) / "src" / "heattree_py" / "_static"
        js_file = static_dir / "heat-tree.iife.min.js"

        # Import and run the download script
        import sys
        scripts_dir = Path(self.root) / "scripts"
        sys.path.insert(0, str(scripts_dir))

        try:
            from download_js import download_js
            result = download_js()
            if result != 0:
                raise RuntimeError("Failed to download JS file")
        finally:
            sys.path.pop(0)
