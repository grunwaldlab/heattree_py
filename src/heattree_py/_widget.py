"""Interactive phylogenetic tree visualization for Jupyter notebooks.

Embeds the `heat-tree` JavaScript widget
(https://github.com/grunwaldlab/heat-tree) into Jupyter notebooks.

When used in Jupyter, the JS library is loaded once on import and shared
by all widgets. In other environments, the embed parameter controls
whether JS is bundled per-widget or loaded from CDN.
"""

import json
import re
import uuid
from pathlib import Path

import pandas as pd

from heattree_py import HEAT_TREE_JS_VERSION

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CDN_URL = (
    "https://unpkg.com/@grunwaldlab/heat-tree"
    f"@{HEAT_TREE_JS_VERSION}/dist/heat-tree.iife.min.js"
)
"""CDN URL for the self-contained IIFE build of the heat-tree widget."""


# ---------------------------------------------------------------------------
# Environment Detection
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# JS Content Access
# ---------------------------------------------------------------------------


def _get_embedded_js():
    """Get the bundled JS content for offline embedding.

    Returns:
        The minified JS code as a string.

    Raises:
        FileNotFoundError: If the bundled JS file does not exist.
    """
    from heattree_py._static import get_js_content

    return get_js_content()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _to_newick(tree):
    """Convert a tree input to a Newick-format string."""
    if tree is None:
        return None

    # --- file path --------------------------------------------------------
    if isinstance(tree, Path):
        if not tree.is_file():
            raise FileNotFoundError(f"Tree file not found: {tree}")
        return tree.read_text().strip()

    if isinstance(tree, str):
        path = Path(tree)
        if path.is_file():
            return path.read_text().strip()
        # Assume it is a Newick string.
        return tree

    # --- ete3 -------------------------------------------------------------
    try:
        import ete3

        if isinstance(tree, ete3.TreeNode):
            return tree.write(format=1)
    except ImportError:
        pass

    # --- dendropy ---------------------------------------------------------
    try:
        import dendropy

        if isinstance(tree, dendropy.Tree):
            return tree.as_string(schema="newick").strip()
    except ImportError:
        pass

    # --- Biopython --------------------------------------------------------
    try:
        from io import StringIO

        from Bio import Phylo
        from Bio.Phylo import BaseTree

        if isinstance(tree, BaseTree.Tree):
            buf = StringIO()
            Phylo.write(tree, buf, "newick")
            return buf.getvalue().strip()
    except ImportError:
        pass

    # --- scikit-bio -------------------------------------------------------
    try:
        from io import StringIO

        import skbio

        if isinstance(tree, skbio.TreeNode):
            buf = StringIO()
            tree.write(buf, format="newick")
            return buf.getvalue().strip()
    except ImportError:
        pass

    raise TypeError(
        f"Unsupported tree type: {type(tree).__name__}. "
        "Expected a Newick string, file path, ete3.TreeNode, "
        "dendropy.Tree, Bio.Phylo tree, or skbio.TreeNode."
    )


def _df_to_tsv(df):
    """Convert a DataFrame to a TSV string."""
    if not isinstance(df.index, pd.RangeIndex):
        df = df.reset_index()
    return df.fillna("").to_csv(sep="\t", index=False)


def _to_tsv(metadata):
    """Convert metadata input to a TSV string."""
    if metadata is None:
        return None

    if isinstance(metadata, pd.DataFrame):
        return _df_to_tsv(metadata)

    if isinstance(metadata, Path):
        if not metadata.is_file():
            raise FileNotFoundError(f"Metadata file not found: {metadata}")
        return metadata.read_text()

    if isinstance(metadata, str):
        path = Path(metadata)
        if path.is_file():
            return path.read_text()
        # Assume it is a pre-formatted TSV/CSV string.
        return metadata

    raise TypeError(
        f"Unsupported metadata type: {type(metadata).__name__}. "
        "Expected a pandas DataFrame, file path, or TSV/CSV string."
    )


def _format_tip_labels(labels):
    """Format tip labels for nicer display."""
    if not labels:
        return labels

    labels = list(labels)

    # Replace underscores with spaces if words are short
    word_counts = [len(re.split(r"_+", lbl)) for lbl in labels]
    if sum(word_counts) / len(word_counts) <= 3:
        labels = [re.sub(r"_+", " ", lbl) for lbl in labels]

    # Capitalise first letter if mostly alphabetic and all start lower
    all_chars = "".join(labels).replace(" ", "")
    if all_chars:
        alpha_count = sum(c.isalpha() for c in all_chars)
        alpha_ratio = alpha_count / len(all_chars)
        all_start_lower = all(lbl[0].islower() for lbl in labels if lbl)
        if alpha_ratio > 0.9 and all_start_lower:
            labels = [lbl[0].upper() + lbl[1:] if lbl else lbl for lbl in labels]

    return labels


def _normalise_to_list(value, *, allow_dict=False):
    """Wrap a single value in a list if it is not already one."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if allow_dict and isinstance(value, dict):
        return [value]
    return [value]


# ---------------------------------------------------------------------------
# HTML generation for different modes
# ---------------------------------------------------------------------------


def _build_html_jupyter_embedded(trees_data, options, widget_id, height):
    """Build HTML for Jupyter with shared JS (import-loaded)."""
    trees_json = json.dumps(trees_data)
    options_json = json.dumps(options) if options else "{}"

    error_html = (
        '<div style=\\"padding: 20px; color: red; border: 1px solid #fcc; '
        'background: #fee; border-radius: 4px;\\"><strong>Error:</strong> '
        "heat-tree JavaScript not loaded. Make sure to run "
        "<code>import heattree_py</code> before creating widgets.</div>"
    )

    return f"""<div id="{widget_id}" style="width: 100%; height: {height}; position: relative;"></div>
<script type="text/javascript">
(function() {{
    var container = document.getElementById("{widget_id}");
    if (!container) return;

    if (typeof window.HeatTree === 'undefined') {{
        container.innerHTML = "{error_html}";
        console.error("heattree_py: window.HeatTree is undefined. " +
            "Did you import heattree_py in this notebook?");
        return;
    }}

    try {{
        HeatTree.heatTree("#{widget_id}", {trees_json}, {options_json});
    }} catch (e) {{
        container.innerHTML = "<div style=\\\"padding: 20px; color: red;\\\">" +
            "Error rendering tree: " + e.message + "</div>";
        console.error("heattree_py: Error rendering widget:", e);
    }}
}})();
</script>"""


def _build_html_jupyter_cdn(trees_data, options, widget_id, height):
    """Build HTML for Jupyter that loads JS from CDN."""
    trees_json = json.dumps(trees_data)
    options_json = json.dumps(options) if options else "{}"

    return f"""<div id="{widget_id}" style="width: 100%; height: {height}; position: relative;"></div>
<script type="text/javascript">
(function() {{
    var container = document.getElementById("{widget_id}");
    if (!container) return;

    function render() {{
        try {{
            HeatTree.heatTree("#{widget_id}", {trees_json}, {options_json});
        }} catch (e) {{
            container.innerHTML = "<div style=\\\"padding: 20px; color: red;\\\">" +
                "Error rendering tree: " + e.message + "</div>";
            console.error("heattree_py: Error rendering widget:", e);
        }}
    }}

    if (typeof window.HeatTree === 'undefined') {{
        var script = document.createElement("script");
        script.src = "{CDN_URL}";
        script.onload = render;
        script.onerror = function() {{
            container.innerHTML = "<div style=\\\"padding: 20px; color: red; border: 1px solid #fcc; " +
                "background: #fee; border-radius: 4px;\\\"><strong>Error:</strong> " +
                "Failed to load heat-tree widget from CDN. Check internet or use embed=True.</div>";
        }};
        document.head.appendChild(script);
    }} else {{
        render();
    }}
}})();
</script>"""


def _build_html_standalone_embedded(trees_data, options, widget_id, height):
    """Build HTML for non-Jupyter with embedded JS."""
    trees_json = json.dumps(trees_data)
    options_json = json.dumps(options) if options else "{}"
    js_code = _get_embedded_js()

    return f"""<div id="{widget_id}" style="width: 100%; height: {height}; position: relative;"></div>
<script type="text/javascript">
(function() {{
    var container = document.getElementById("{widget_id}");
    if (!container) return;

    if (typeof window.HeatTree === 'undefined') {{
        try {{
            {js_code}
            if (typeof HeatTree !== 'undefined') {{
                window.HeatTree = HeatTree;
            }}
        }} catch (e) {{
            container.innerHTML = "<div style=\\\"padding: 20px; color: red;\\\">" +
                "Error loading heat-tree library: " + e.message + "</div>";
            console.error("heattree_py: Error loading JS:", e);
            return;
        }}
    }}

    try {{
        HeatTree.heatTree("#{widget_id}", {trees_json}, {options_json});
    }} catch (e) {{
        container.innerHTML = "<div style=\\\"padding: 20px; color: red;\\\">" +
            "Error rendering tree: " + e.message + "</div>";
        console.error("heattree_py: Error rendering widget:", e);
    }}
}})();
</script>"""


def _build_html_standalone_cdn(trees_data, options, widget_id, height):
    """Build HTML for non-Jupyter that loads JS from CDN."""
    trees_json = json.dumps(trees_data)
    options_json = json.dumps(options) if options else "{}"

    return f"""<div id="{widget_id}" style="width: 100%; height: {height}; position: relative;"></div>
<script type="text/javascript">
(function() {{
    var container = document.getElementById("{widget_id}");
    if (!container) return;

    function render() {{
        try {{
            HeatTree.heatTree("#{widget_id}", {trees_json}, {options_json});
        }} catch (e) {{
            container.innerHTML = "<div style=\\\"padding: 20px; color: red;\\\">" +
                "Error rendering tree: " + e.message + "</div>";
            console.error("heattree_py: Error rendering widget:", e);
        }}
    }}

    if (typeof window.HeatTree === 'undefined') {{
        var script = document.createElement("script");
        script.src = "{CDN_URL}";
        script.onload = render;
        script.onerror = function() {{
            container.innerHTML = "<div style=\\\"padding: 20px; color: red; border: 1px solid #fcc; " +
                "background: #fee; border-radius: 4px;\\\"><strong>Error:</strong> " +
                "Failed to load heat-tree widget from CDN. Check internet or use embed=True.</div>";
        }};
        document.head.appendChild(script);
    }} else {{
        render();
    }}
}})();
</script>"""


# ---------------------------------------------------------------------------
# Display object
# ---------------------------------------------------------------------------


class HeatTreeWidget:
    """An interactive phylogenetic tree widget.

    This object uses the ``_repr_html_`` protocol so it is automatically
    rendered when it is the last expression in a Jupyter notebook cell.

    Attributes:
        _embed: Whether the widget was created with embed=True.
        _env: The detected environment ("jupyter", "ipython", or "plain").
    """

    def __init__(self, html, embed, env):
        self._html = html
        self._embed = embed
        self._env = env

    def _repr_html_(self):
        """Return the HTML representation for Jupyter rendering."""
        return self._html

    def to_html(self):
        """Return the raw HTML string."""
        return self._html

    def save(self, path):
        """Save as a standalone HTML file."""
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Heat Tree Visualization</title>
<style>
body {{
    margin: 0;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
}}
h1 {{
    font-size: 1.5em;
    margin-bottom: 1em;
}}
</style>
</head>
<body>
<h1>Heat Tree Visualization</h1>
{self._html}
</body>
</html>"""
        Path(path).write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def heat_tree(
    tree=None,
    metadata=None,
    aesthetics=None,
    *,
    embed=True,
    width="100%",
    height="500px",
    **options,
):
    """Create an interactive phylogenetic tree visualisation.

    In Jupyter environments, the JavaScript library is automatically
    loaded when ``heattree_py`` is imported. All widgets in the same
    notebook share this single JS load, making widget outputs small
    and efficient.

    In non-Jupyter environments (plain Python, IPython terminal), the
    ``embed`` parameter controls whether the JS is bundled with each
    widget (for offline use) or loaded from CDN.
    """
    if not isinstance(embed, bool):
        raise TypeError("embed must be a boolean")

    # Detect environment
    env = _detect_jupyter()

    # -- Normalise inputs to lists -----------------------------------------
    tree_list = _normalise_to_list(tree)
    metadata_list = _normalise_to_list(metadata)
    aesthetics_list = _normalise_to_list(aesthetics, allow_dict=True)

    # -- Build per-tree data structures ------------------------------------
    trees_data = []

    if tree_list is not None:
        for i, t in enumerate(tree_list):
            newick = _to_newick(t)
            tree_obj = {
                "name": f"tree {i + 1}",
                "newick": newick,
            }

            # Metadata
            if metadata_list is not None and i < len(metadata_list):
                meta_raw = metadata_list[i]
                if meta_raw is not None:
                    cur_aesthetics = None
                    if aesthetics_list and i < len(aesthetics_list):
                        cur_aesthetics = aesthetics_list[i]
                    if cur_aesthetics is None:
                        cur_aesthetics = {}

                    if isinstance(meta_raw, pd.DataFrame) and not isinstance(
                        meta_raw.index, pd.RangeIndex
                    ):
                        meta_df = meta_raw.reset_index()
                        idx_col = meta_df.columns[0]
                        if "tipLabelText" not in cur_aesthetics:
                            formatted = _format_tip_labels(
                                meta_df[idx_col].astype(str).tolist()
                            )
                            meta_df["formatted_label"] = formatted
                            cur_aesthetics = {
                                **cur_aesthetics,
                                "tipLabelText": "formatted_label",
                            }
                        tsv = meta_df.fillna("").to_csv(sep="\t", index=False)
                    else:
                        tsv = _to_tsv(meta_raw)

                    meta_name = f"metadata {i + 1}"
                    tree_obj["metadata"] = [{"name": meta_name, "data": tsv}]

                    if aesthetics_list and i < len(aesthetics_list):
                        aesthetics_list[i] = cur_aesthetics
                    elif cur_aesthetics:
                        if aesthetics_list is None:
                            aesthetics_list = [None] * len(tree_list)
                        if i < len(aesthetics_list):
                            aesthetics_list[i] = cur_aesthetics

            # Aesthetics
            if (
                aesthetics_list is not None
                and i < len(aesthetics_list)
                and aesthetics_list[i]
            ):
                aes = aesthetics_list[i]
                if "metadata" in tree_obj:
                    tree_obj["aesthetics"] = aes

            trees_data.append(tree_obj)

    # -- Generate HTML -----------------------------------------------------
    widget_id = f"heat-tree-{uuid.uuid4().hex[:12]}"

    if env == "jupyter":
        if embed:
            html = _build_html_jupyter_embedded(trees_data, options, widget_id, height)
        else:
            html = _build_html_jupyter_cdn(trees_data, options, widget_id, height)
    else:
        if embed:
            html = _build_html_standalone_embedded(trees_data, options, widget_id, height)
        else:
            html = _build_html_standalone_cdn(trees_data, options, widget_id, height)

    return HeatTreeWidget(html, embed, env)
