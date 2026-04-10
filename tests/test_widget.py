"""Tests for heattree_py._widget."""

import pandas as pd
import pytest

from heattree_py import HEAT_TREE_JS_VERSION
from heattree_py._widget import (
    CDN_URL,
    HeatTreeWidget,
    _build_html_jupyter_cdn,
    _build_html_jupyter_embedded,
    _build_html_standalone_cdn,
    _build_html_standalone_embedded,
    _detect_jupyter,
    _df_to_tsv,
    _format_tip_labels,
    _get_embedded_js,
    _to_newick,
    _to_tsv,
    heat_tree,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"


@pytest.fixture()
def simple_metadata():
    """A small metadata DataFrame with an explicit ID column."""
    return pd.DataFrame(
        {
            "node_id": ["A", "B", "C", "D"],
            "group": ["x", "x", "y", "y"],
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )


@pytest.fixture()
def indexed_metadata():
    """A metadata DataFrame whose index contains node IDs."""
    return pd.DataFrame(
        {
            "group": ["x", "x", "y", "y"],
            "value": [1.0, 2.0, 3.0, 4.0],
        },
        index=pd.Index(
            ["species_alpha", "species_beta", "species_gamma", "species_delta"],
            name="node_id",
        ),
    )


@pytest.fixture()
def newick_file(tmp_path):
    """Write a Newick string to a temporary file and return the path."""
    p = tmp_path / "tree.nwk"
    p.write_text(SIMPLE_NEWICK)
    return p


@pytest.fixture()
def tsv_file(tmp_path):
    """Write a small TSV to a temporary file and return the path."""
    content = "node_id\tgroup\nA\tx\nB\tx\nC\ty\nD\ty\n"
    p = tmp_path / "meta.tsv"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Environment Detection
# ---------------------------------------------------------------------------


class TestDetectJupyter:
    """Tests for the _detect_jupyter helper."""

    def test_returns_string(self):
        """Should return a string value."""
        result = _detect_jupyter()
        assert isinstance(result, str)
        assert result in ("jupyter", "ipython", "plain")

    def test_plain_python(self):
        """Should detect plain Python when IPython not available."""
        # This test runs in plain pytest, so should be "plain"
        result = _detect_jupyter()
        assert result == "plain"


# ---------------------------------------------------------------------------
# _to_newick
# ---------------------------------------------------------------------------


class TestToNewick:
    """Tests for the _to_newick helper."""

    def test_newick_string(self):
        """A plain Newick string is returned as-is."""
        assert _to_newick(SIMPLE_NEWICK) == SIMPLE_NEWICK

    def test_none_returns_none(self):
        """None input yields None output."""
        assert _to_newick(None) is None

    def test_file_path_str(self, newick_file):
        """A string path to a Newick file is read and stripped."""
        result = _to_newick(str(newick_file))
        assert result == SIMPLE_NEWICK

    def test_file_path_pathlib(self, newick_file):
        """A pathlib.Path to a Newick file is read and stripped."""
        result = _to_newick(newick_file)
        assert result == SIMPLE_NEWICK

    def test_missing_file_path_raises(self, tmp_path):
        """A Path to a non-existent file raises FileNotFoundError."""
        from pathlib import Path

        with pytest.raises(FileNotFoundError):
            _to_newick(Path(tmp_path / "does_not_exist.nwk"))

    def test_unsupported_type_raises(self):
        """An unsupported type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported tree type"):
            _to_newick(12345)


# ---------------------------------------------------------------------------
# _df_to_tsv / _to_tsv
# ---------------------------------------------------------------------------


class TestDfToTsv:
    """Tests for _df_to_tsv."""

    def test_basic_dataframe(self, simple_metadata):
        """A DataFrame with default index produces correct TSV."""
        tsv = _df_to_tsv(simple_metadata)
        lines = tsv.strip().split("\n")
        assert lines[0] == "node_id\tgroup\tvalue"
        assert len(lines) == 5  # header + 4 rows

    def test_non_default_index_included(self, indexed_metadata):
        """A DataFrame with a named index has the index added as a column."""
        tsv = _df_to_tsv(indexed_metadata)
        lines = tsv.strip().split("\n")
        # The index column should appear first after reset_index.
        assert "node_id" in lines[0]
        assert "species_alpha" in lines[1]


class TestToTsv:
    """Tests for the _to_tsv helper."""

    def test_none_returns_none(self):
        assert _to_tsv(None) is None

    def test_dataframe(self, simple_metadata):
        tsv = _to_tsv(simple_metadata)
        assert "node_id" in tsv
        assert "A" in tsv

    def test_file_path_str(self, tsv_file):
        tsv = _to_tsv(str(tsv_file))
        assert "node_id" in tsv

    def test_file_path_pathlib(self, tsv_file):
        tsv = _to_tsv(tsv_file)
        assert "node_id" in tsv

    def test_raw_tsv_string(self):
        raw = "col1\tcol2\na\t1\n"
        assert _to_tsv(raw) == raw

    def test_missing_file_raises(self, tmp_path):
        from pathlib import Path

        with pytest.raises(FileNotFoundError):
            _to_tsv(Path(tmp_path / "missing.tsv"))

    def test_unsupported_type_raises(self):
        with pytest.raises(TypeError, match="Unsupported metadata type"):
            _to_tsv(12345)


# ---------------------------------------------------------------------------
# _format_tip_labels
# ---------------------------------------------------------------------------


class TestFormatTipLabels:
    """Tests for the _format_tip_labels helper."""

    def test_empty_list(self):
        assert _format_tip_labels([]) == []

    def test_underscore_replacement(self):
        labels = ["hello_world", "foo_bar"]
        result = _format_tip_labels(labels)
        assert result == ["Hello world", "Foo bar"]

    def test_no_replacement_many_words(self):
        labels = ["a_b_c_d_e", "x_y_z_w_v"]
        result = _format_tip_labels(labels)
        # Mean word count > 3 so underscores are kept.
        assert all("_" in lbl for lbl in result)

    def test_capitalisation(self):
        labels = ["alpha", "beta"]
        result = _format_tip_labels(labels)
        assert result == ["Alpha", "Beta"]

    def test_no_capitalisation_if_uppercase(self):
        labels = ["Alpha", "Beta"]
        result = _format_tip_labels(labels)
        # Already capitalised; all_start_lower is False.
        assert result == ["Alpha", "Beta"]


# ---------------------------------------------------------------------------
# HTML generation helpers
# ---------------------------------------------------------------------------


class TestBuildHtmlJupyterEmbedded:
    """Tests for _build_html_jupyter_embedded."""

    def test_contains_widget_div(self):
        """HTML should contain the widget container div."""
        html = _build_html_jupyter_embedded([], {}, "my-widget", "500px")
        assert 'id="my-widget"' in html
        assert "div" in html

    def test_contains_tree_data(self):
        """Tree data should be in the HTML."""
        data = [{"name": "t1", "newick": "(A,B);"}]
        html = _build_html_jupyter_embedded(data, {}, "w", "500px")
        assert "(A,B);" in html

    def test_contains_options(self):
        """Options should be in the HTML."""
        html = _build_html_jupyter_embedded([], {"layout": "circular"}, "w", "500px")
        assert '"circular"' in html

    def test_checks_for_heat_tree_global(self):
        """HTML should check if HeatTree is loaded."""
        html = _build_html_jupyter_embedded([], {}, "w", "500px")
        assert "typeof window.HeatTree" in html

    def test_error_message_on_missing_js(self):
        """HTML should show error if JS not loaded."""
        html = _build_html_jupyter_embedded([], {}, "w", "500px")
        assert "heat-tree JavaScript not loaded" in html
        assert "import heattree_py" in html


class TestBuildHtmlJupyterCdn:
    """Tests for _build_html_jupyter_cdn."""

    def test_contains_cdn_url(self):
        """CDN HTML should reference the CDN URL."""
        html = _build_html_jupyter_cdn([], {}, "test-id", "500px")
        assert CDN_URL in html

    def test_contains_widget_div(self):
        """HTML should contain the widget container div."""
        html = _build_html_jupyter_cdn([], {}, "my-widget", "500px")
        assert 'id="my-widget"' in html

    def test_contains_tree_data(self):
        """Tree data should be in the HTML."""
        data = [{"name": "t1", "newick": "(A,B);"}]
        html = _build_html_jupyter_cdn(data, {}, "w", "500px")
        assert "(A,B);" in html

    def test_lazy_loading_script(self):
        """CDN HTML should create a script element for lazy loading."""
        html = _build_html_jupyter_cdn([], {}, "w", "500px")
        assert "document.createElement" in html
        assert "typeof window.HeatTree" in html


class TestBuildHtmlStandaloneEmbedded:
    """Tests for _build_html_standalone_embedded."""

    def test_contains_js_code(self):
        """Embedded HTML should contain the JS library code."""
        html = _build_html_standalone_embedded([], {}, "test-id", "500px")
        # The JS code should be inlined (substantial content)
        assert len(html) > 10000  # Should be substantial with JS

    def test_contains_widget_div(self):
        """HTML should contain the widget container div."""
        html = _build_html_standalone_embedded([], {}, "my-widget", "500px")
        assert 'id="my-widget"' in html

    def test_contains_tree_data(self):
        """Tree data should be in the HTML."""
        data = [{"name": "t1", "newick": "(A,B);"}]
        html = _build_html_standalone_embedded(data, {}, "w", "500px")
        assert "(A,B);" in html


class TestBuildHtmlStandaloneCdn:
    """Tests for _build_html_standalone_cdn."""

    def test_contains_cdn_url(self):
        """CDN HTML should reference the CDN URL."""
        html = _build_html_standalone_cdn([], {}, "test-id", "500px")
        assert CDN_URL in html

    def test_contains_widget_div(self):
        """HTML should contain the widget container div."""
        html = _build_html_standalone_cdn([], {}, "my-widget", "500px")
        assert 'id="my-widget"' in html

    def test_contains_tree_data(self):
        """Tree data should be in the HTML."""
        data = [{"name": "t1", "newick": "(A,B);"}]
        html = _build_html_standalone_cdn(data, {}, "w", "500px")
        assert "(A,B);" in html


# ---------------------------------------------------------------------------
# Embedded JS bundle
# ---------------------------------------------------------------------------


class TestGetEmbeddedJs:
    """Tests for _get_embedded_js."""

    def test_returns_js_content(self):
        """Should return the JS file contents."""
        js = _get_embedded_js()
        assert len(js) > 1000  # Should be substantial
        assert "function" in js or "var" in js

    def test_js_version_matches(self):
        """The bundled JS should match the version constant."""
        assert HEAT_TREE_JS_VERSION == "0.2.0"


# ---------------------------------------------------------------------------
# HeatTreeWidget display object
# ---------------------------------------------------------------------------


class TestHeatTreeWidget:
    """Tests for the HeatTreeWidget display object."""

    def test_repr_html(self):
        widget = HeatTreeWidget("<p>test</p>", embed=True, env="plain")
        assert widget._repr_html_() == "<p>test</p>"

    def test_to_html(self):
        widget = HeatTreeWidget("<p>test</p>", embed=True, env="plain")
        assert widget.to_html() == "<p>test</p>"

    def test_embed_attribute(self):
        widget = HeatTreeWidget("<p>test</p>", embed=True, env="plain")
        assert widget._embed is True
        widget2 = HeatTreeWidget("<p>test</p>", embed=False, env="plain")
        assert widget2._embed is False

    def test_env_attribute(self):
        widget = HeatTreeWidget("<p>test</p>", embed=True, env="jupyter")
        assert widget._env == "jupyter"

    def test_save(self, tmp_path):
        html = "<div>widget content</div>"
        widget = HeatTreeWidget(html, embed=True, env="plain")
        out = tmp_path / "widget.html"
        widget.save(out)
        content = out.read_text()
        assert "widget content" in content
        assert "<!DOCTYPE html>" in content


# ---------------------------------------------------------------------------
# heat_tree (integration)
# ---------------------------------------------------------------------------


class TestHeatTree:
    """Integration tests for the public heat_tree function."""

    def test_returns_widget(self):
        """heat_tree returns a HeatTreeWidget instance."""
        result = heat_tree()
        assert isinstance(result, HeatTreeWidget)

    def test_default_embed_true(self):
        """Default embed mode is True."""
        result = heat_tree()
        assert result._embed is True

    def test_embed_false(self):
        """embed=False should set embed attribute to False."""
        result = heat_tree(embed=False)
        assert result._embed is False

    def test_detects_plain_environment(self):
        """In plain Python, should detect plain environment."""
        result = heat_tree()
        assert result._env == "plain"

    def test_simple_tree_embedded(self):
        """A Newick string with embed=True should work."""
        html = heat_tree(SIMPLE_NEWICK, embed=True).to_html()
        assert "div" in html
        assert "A:0.1" in html

    def test_simple_tree_cdn(self):
        """A Newick string with embed=False should use CDN."""
        html = heat_tree(SIMPLE_NEWICK, embed=False).to_html()
        assert CDN_URL in html

    def test_with_metadata(self, simple_metadata):
        """Metadata is serialised into the widget data."""
        html = heat_tree(
            SIMPLE_NEWICK,
            metadata=simple_metadata,
            aesthetics={"tipLabelColor": "group"},
        ).to_html()
        assert "tipLabelColor" in html

    def test_with_options(self):
        """Extra keyword arguments are passed as widget options."""
        html = heat_tree(SIMPLE_NEWICK, layout="circular").to_html()
        assert "circular" in html

    def test_multiple_trees(self):
        """A list of trees produces entries for each tree."""
        t1 = "(A,B);"
        t2 = "(C,D);"
        html = heat_tree([t1, t2]).to_html()
        assert "(A,B);" in html
        assert "(C,D);" in html

    def test_file_path_tree(self, newick_file):
        """A file path is read and embedded."""
        html = heat_tree(str(newick_file)).to_html()
        assert "A:0.1" in html

    def test_indexed_metadata_creates_formatted_labels(self, indexed_metadata):
        """A non-default index triggers formatted tip labels."""
        newick = "(species_alpha,species_beta,(species_gamma,species_delta));"
        html = heat_tree(newick, metadata=indexed_metadata).to_html()
        assert "formatted_label" in html
        assert "tipLabelText" in html

    def test_embed_must_be_boolean(self):
        """embed parameter must be a boolean."""
        with pytest.raises(TypeError, match="embed must be a boolean"):
            heat_tree(embed="yes")
