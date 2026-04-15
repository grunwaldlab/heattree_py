"""Tests for heattree_py example data loading.

This module tests the example_data function for loading bundled datasets.
"""

from pathlib import Path

from heattree_py import example_data


class TestExampleDataLoading:
    """Test loading example datasets."""

    def test_example_data_listing(self, capsys):
        """Test that example_data() lists available datasets."""
        result = example_data()
        captured = capsys.readouterr()
        assert result is None  # Prints to stdout
        assert "Available datasets" in captured.out

    def test_example_data_valid_tree(self):
        """Test getting path to valid tree datasets."""
        path = example_data("weisberg_2020_mlsa")
        assert isinstance(path, Path)
        assert path.exists()
        assert path.suffix == ".tre"

    def test_example_data_valid_metadata(self):
        """Test getting path to valid metadata datasets."""
        path = example_data("weisberg_2020_metadata")
        assert isinstance(path, Path)
        assert path.exists()
        assert path.suffix == ".tsv"

    def test_example_data_invalid_name(self, capsys):
        """Test handling of invalid dataset name."""
        result = example_data("nonexistent")
        captured = capsys.readouterr()
        assert result is None  # Prints error and returns None
        assert "Unknown dataset" in captured.out
