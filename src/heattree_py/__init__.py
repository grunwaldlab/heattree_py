"""Interactive phylogenetic tree visualisation for Jupyter notebooks.

``heattree_py`` embeds the JavaScript
`heat-tree <https://github.com/grunwaldlab/heat-tree>`_ widget into
Jupyter notebooks via the ``_repr_html_`` display protocol (the same
mechanism used by ``IPython.display.HTML``).  The resulting output is
fully self-contained and works in static HTML exports of the notebook
(no running Python kernel required).

When imported in a Jupyter environment, the JavaScript library is
automatically loaded once and shared by all widgets. In non-Jupyter
environments, the ``embed`` parameter controls whether the JS is
bundled with each widget or loaded from CDN.
"""

__version__ = "0.1.0"
HEAT_TREE_JS_VERSION = "0.3.0"
"""Version of the ``@grunwaldlab/heat-tree`` npm package used."""


def _detect_jupyter():
    """Detect if running in a Jupyter/IPython environment.

    Returns:
        "jupyter" - Running in Jupyter Notebook/Lab/VS Code/Colab
        "ipython" - Running in IPython terminal (no display)
        "plain"   - Running in plain Python
    """
    try:
        from IPython import get_ipython

        ipython = get_ipython()

        if ipython is None:
            return "plain"

        # Check if we can display (not terminal-only IPython)
        if hasattr(ipython, "kernel"):
            return "jupyter"

        # Check for IPKernelApp in config (indicates notebook)
        if hasattr(ipython, "config") and "IPKernelApp" in getattr(
            ipython, "config", {}
        ):
            return "jupyter"

        return "ipython"  # IPython terminal, no display capability

    except ImportError:
        return "plain"


def _load_js_on_import():
    """Load the heat-tree JS into the Jupyter DOM on import.

    This function is called automatically when heattree_py is imported
    in a Jupyter environment. It injects the JavaScript library once,
    which is then shared by all widgets in the notebook.
    """
    try:
        from IPython.display import HTML, display

        from heattree_py._static import get_js_content

        js_code = get_js_content()
        # Inject JS with idempotent check using HTML (not Javascript)
        # This ensures the script runs in the global scope immediately
        display(
            HTML(
                f"""<script type="text/javascript">
(function() {{
    if (typeof window.HeatTree === 'undefined') {{
        try {{
            {js_code}
            if (typeof HeatTree !== 'undefined') {{
                window.HeatTree = HeatTree;
            }}
        }} catch(e) {{
            console.error('heattree_py: Failed to load JS:', e);
        }}
    }}
}})();
</script>"""
            ),
            display_id="heattree_js_init",
        )
    except Exception as e:
        # Silently fail - widgets will handle missing JS with error message
        import warnings

        warnings.warn(
            f"Could not auto-load heat-tree JavaScript on import: {e}",
            RuntimeWarning,
            stacklevel=2,
        )


# Auto-load JS if in Jupyter environment
if _detect_jupyter() == "jupyter":
    _load_js_on_import()


from heattree_py._widget import HeatTreeWidget, heat_tree  # noqa: E402
from heattree_py.data import example_data  # noqa: E402

__all__ = [
    "HEAT_TREE_JS_VERSION",
    "HeatTreeWidget",
    "__version__",
    "example_data",
    "heat_tree",
]
