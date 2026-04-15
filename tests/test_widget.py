"""Tests for heattree_py._widget.

Tests focus on public APIs and verify actual DOM rendering via Playwright.
Trivial implementation details are not tested.
"""

import pandas as pd
import pytest

from heattree_py import example_data, heat_tree
from heattree_py._widget import HeatTreeWidget, _to_newick

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
def newick_file(tmp_path):
    """Write a Newick string to a temporary file and return the path."""
    p = tmp_path / "tree.nwk"
    p.write_text(SIMPLE_NEWICK)
    return p


@pytest.fixture()
def widget_with_tree(monkeypatch):
    """Create a widget using heat_tree() and return it."""

    def mock_open(url, new=0):
        return True

    monkeypatch.setattr("webbrowser.open", mock_open)

    widget = heat_tree(SIMPLE_NEWICK, open_browser=True)
    assert widget._temp_path is not None
    return widget


@pytest.fixture()
def widget_with_metadata(monkeypatch):
    """Create a widget with metadata using heat_tree() API."""

    def mock_open(url, new=0):
        return True

    monkeypatch.setattr("webbrowser.open", mock_open)

    metadata = pd.DataFrame(
        {
            "node_id": ["A", "B", "C", "D"],
            "group": ["x", "y", "x", "y"],
        }
    )

    widget = heat_tree(
        SIMPLE_NEWICK,
        metadata=metadata,
        aesthetics={"tipLabelText": "node_id", "tipLabelColor": "group"},
        open_browser=True,
    )

    assert widget._temp_path is not None
    return widget


# ---------------------------------------------------------------------------
# Tree conversion (complex private function)
# ---------------------------------------------------------------------------


class TestToNewick:
    """Tests for the _to_newick helper - complex multi-format conversion."""

    def test_newick_string_passthrough(self):
        """A plain Newick string is returned as-is."""
        assert _to_newick(SIMPLE_NEWICK) == SIMPLE_NEWICK

    def test_file_path_read(self, newick_file):
        """A file path is read and content returned."""
        result = _to_newick(str(newick_file))
        assert result == SIMPLE_NEWICK

    def test_missing_file_raises(self, tmp_path):
        """A Path to a non-existent file raises FileNotFoundError."""
        from pathlib import Path

        with pytest.raises(FileNotFoundError):
            _to_newick(Path(tmp_path / "does_not_exist.nwk"))

    def test_unsupported_type_raises(self):
        """An unsupported type raises TypeError with helpful message."""
        with pytest.raises(TypeError, match="Unsupported tree type"):
            _to_newick(12345)


# ---------------------------------------------------------------------------
# HeatTreeWidget class methods
# ---------------------------------------------------------------------------


class TestHeatTreeWidget:
    """Tests for the HeatTreeWidget display object."""

    def test_save_creates_file(self, tmp_path):
        """save() creates a standalone HTML file."""
        html = "<div>widget content</div>"
        widget = HeatTreeWidget(html, embed=True, env="plain")
        out = tmp_path / "widget.html"
        widget.save(out)
        content = out.read_text()
        assert "widget content" in content
        assert "<!DOCTYPE html>" in content

    def test_show_creates_temp_file_and_opens_browser(self, monkeypatch):
        """show() creates temp file and opens browser."""
        opened_urls = []

        def mock_open(url, new=0):
            opened_urls.append(url)
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        widget = HeatTreeWidget("<div>test</div>", embed=True, env="plain")
        path = widget.show()

        assert path.exists()
        assert "<div>test</div>" in path.read_text()
        assert len(opened_urls) == 1

        # Clean up
        path.unlink()


# ---------------------------------------------------------------------------
# Browser-based tests for heat_tree function
# ---------------------------------------------------------------------------


@pytest.mark.browser
@pytest.mark.slow
class TestHeatTreeRendering:
    """Test heat_tree rendering in browser using Playwright."""

    def test_svg_container_created(self, page, widget_with_tree):
        """Tree rendering should create an SVG container."""
        page.goto(f"file://{widget_with_tree._temp_path}")
        page.wait_for_selector("svg", state="attached", timeout=10000)
        assert page.locator("svg").count() > 0

    def test_tree_structure_rendered(self, page, widget_with_tree):
        """Tree should have all expected DOM elements."""
        page.goto(f"file://{widget_with_tree._temp_path}")
        page.wait_for_selector(".tree-elements", state="attached", timeout=10000)

        # Check all layers exist
        assert page.locator(".branch-layer").count() > 0
        assert page.locator(".node-layer").count() > 0

        # Check content
        assert page.locator(".branch-group").count() >= 3
        assert page.locator(".node").count() >= 4

    def test_tips_have_labels_with_names(self, page, widget_with_tree):
        """Tip labels should show node names A, B, C, D."""
        page.goto(f"file://{widget_with_tree._temp_path}")
        page.wait_for_selector(".tip-label", state="attached", timeout=10000)

        tip_labels = page.locator(".tip-label")
        assert tip_labels.count() >= 4

        labels_text = tip_labels.all_text_contents()
        labels_joined = " ".join(labels_text)
        assert "A" in labels_joined
        assert "B" in labels_joined
        assert "C" in labels_joined
        assert "D" in labels_joined


@pytest.mark.browser
@pytest.mark.slow
class TestHeatTreeMetadata:
    """Test metadata rendering in browser."""

    def test_metadata_text_appears_in_labels(self, page, widget_with_metadata):
        """tipLabelText mapping should show metadata values."""
        page.goto(f"file://{widget_with_metadata._temp_path}")
        page.wait_for_selector(".tip-label", state="attached", timeout=10000)

        labels_text = page.locator(".tip-label").all_text_contents()
        labels_joined = " ".join(labels_text)

        assert "A" in labels_joined
        assert "B" in labels_joined
        assert "C" in labels_joined
        assert "D" in labels_joined

    def test_metadata_color_applied(self, page, widget_with_metadata):
        """tipLabelColor mapping should apply fill colors."""
        page.goto(f"file://{widget_with_metadata._temp_path}")
        page.wait_for_selector(".tip-label", state="attached", timeout=10000)

        labels = page.locator(".tip-label")
        assert labels.count() >= 4

        # Check that labels have fill style set
        first_label = labels.first
        fill_value = first_label.evaluate(
            "el => el.style.fill || getComputedStyle(el).fill"
        )
        assert fill_value is not None


@pytest.mark.browser
@pytest.mark.slow
class TestHeatTreeOptions:
    """Test heat_tree options rendering in browser."""

    def test_circular_layout_renders(self, page, monkeypatch):
        """Circular layout should create valid tree DOM."""

        def mock_open(url, new=0):
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        widget = heat_tree(SIMPLE_NEWICK, layout="circular", open_browser=True)

        page.goto(f"file://{widget._temp_path}")
        page.wait_for_selector(".tree-elements", state="attached", timeout=10000)

        assert page.locator("svg").count() > 0
        assert page.locator(".node").count() >= 4
        assert page.locator(".branch-group").count() >= 3

    def test_multiple_trees_render(self, page, monkeypatch):
        """Multiple trees should render correctly."""

        def mock_open(url, new=0):
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        widget = heat_tree(["(A,B);", "(C,D);"], open_browser=True)

        page.goto(f"file://{widget._temp_path}")
        page.wait_for_selector(".tree-elements", state="attached", timeout=10000)

        assert page.locator(".node").count() >= 2

        labels_text = page.locator(".tip-label").all_text_contents()
        labels_joined = " ".join(labels_text)
        has_ab = "A" in labels_joined and "B" in labels_joined
        has_cd = "C" in labels_joined and "D" in labels_joined
        assert has_ab or has_cd


# ---------------------------------------------------------------------------
# Validation and error handling tests (no browser needed)
# ---------------------------------------------------------------------------


class TestHeatTreeValidation:
    """Test input validation."""

    def test_embed_must_be_boolean(self):
        """embed parameter must be a boolean."""
        with pytest.raises(TypeError, match="embed must be a boolean"):
            heat_tree(embed="yes")

    def test_open_browser_must_be_boolean(self):
        """open_browser parameter must be a boolean."""
        with pytest.raises(TypeError, match="open_browser must be a boolean"):
            heat_tree(open_browser="yes")

    def test_tree_names_must_be_list(self):
        """tree_names must be a list or tuple."""
        with pytest.raises(TypeError, match="tree_names must be a list or tuple"):
            heat_tree(["(A,B);", "(C,D);"], tree_names="invalid")

    def test_tree_names_length_must_match(self):
        """tree_names length must match number of trees."""
        with pytest.raises(ValueError, match="tree_names length"):
            heat_tree(["(A,B);", "(C,D);"], tree_names=["OnlyOneName"])


class TestHeatTreeInputTypes:
    """Test different tree and metadata input types."""

    def test_tree_input_types(self, newick_file, monkeypatch):
        """Various tree input types should all work."""

        def mock_open(url, new=0):
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        # Test Newick string
        widget = heat_tree("(A,B,C,D);", open_browser=True)
        assert widget._temp_path is not None

        # Test Path object
        widget = heat_tree(example_data("bansal_2021_tree"), open_browser=True)
        assert widget._temp_path is not None

        # Test string path
        widget = heat_tree(str(newick_file), open_browser=True)
        assert widget._temp_path is not None

    def test_metadata_input_types(self, monkeypatch):
        """Various metadata input types should work."""

        def mock_open(url, new=0):
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        tree = example_data("bansal_2021_tree")
        meta = example_data("bansal_2021_metadata")

        # Test Path object
        widget = heat_tree(
            tree,
            metadata=meta,
            aesthetics={"tipLabelColor": "Lifestyle"},
            open_browser=True,
        )
        assert widget._temp_path is not None

        # Test DataFrame
        df = pd.read_csv(meta, sep="\t")
        widget = heat_tree(
            tree,
            metadata=df,
            aesthetics={"tipLabelColor": "Lifestyle"},
            open_browser=True,
        )
        assert widget._temp_path is not None

        # Test TSV string
        tsv = "node_id\tgroup\nA\tx\nB\ty\n"
        widget = heat_tree(
            "(A:1,B:2);",
            metadata=tsv,
            aesthetics={"tipLabelColor": "group"},
            open_browser=True,
        )
        assert widget._temp_path is not None


class TestHeatTreeErrors:
    """Test error handling."""

    def test_nonexistent_file_path_raises(self):
        """Path to non-existent file raises FileNotFoundError."""
        from pathlib import Path

        with pytest.raises(FileNotFoundError):
            heat_tree(Path("/path/to/nonexistent/tree.nwk"), open_browser=False)

        tree_path = example_data("bansal_2021_tree")
        with pytest.raises(FileNotFoundError):
            heat_tree(
                tree_path,
                metadata=Path("/path/to/nonexistent/meta.tsv"),
                open_browser=False,
            )


class TestHeatTreeExternalLibraries:
    """Test with external phylogenetics libraries."""

    def test_ete3_tree(self, monkeypatch):
        """Test heat_tree with ete3 TreeNode."""
        ete3 = pytest.importorskip("ete3", reason="ete3 not installed")

        def mock_open(url, new=0):
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        tree = ete3.Tree("(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);")
        widget = heat_tree(tree, open_browser=True)
        assert widget._temp_path is not None

    def test_dendropy_tree(self, monkeypatch):
        """Test heat_tree with dendropy Tree."""
        dendropy = pytest.importorskip("dendropy", reason="dendropy not installed")

        def mock_open(url, new=0):
            return True

        monkeypatch.setattr("webbrowser.open", mock_open)

        tree = dendropy.Tree.get(
            data="(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);", schema="newick"
        )
        widget = heat_tree(tree, open_browser=True)
        assert widget._temp_path is not None
