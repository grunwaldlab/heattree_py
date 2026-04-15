"""Example datasets bundled with heattree_py.

This module provides access to example phylogenetic trees and metadata
for use in tutorials and testing.
"""

from pathlib import Path

_DATA_DIR = Path(__file__).parent

# Dataset descriptions adapted from the R heattree package
_DATASET_INFO = {
    "bansal_2021_tree": {
        "filename": "bansal_2021_tree.nwk",
        "description": (
            "A core gene phylogeny of Xylella and related genera from Bansal et al. 2021."
        ),
        "format": "Newick",
    },
    "bansal_2021_metadata": {
        "filename": "bansal_2021_metadata.tsv",
        "description": (
            "Metadata of Xylella and related genera from Bansal et al. 2021."
        ),
        "format": "TSV",
    },
    "weisberg_2020_mlsa": {
        "filename": "weisberg_2020_mlsa.tre",
        "description": (
            "A MLSA (Multi-Locus Sequence Analysis) phylogeny of agrobacterial strains from Weisberg et al. 2020."
        ),
        "format": "Newick",
    },
    "weisberg_2020_beast": {
        "filename": "weisberg_2020_beast.tre",
        "description": (
            "A BEAST phylogeny of agrobacterial strains from Weisberg et al. 2020. "
        ),
        "format": "Newick",
    },
    "weisberg_2020_metadata": {
        "filename": "weisberg_2020_metadata.tsv",
        "description": ("Metadata of agrobacterial strains from Weisberg et al. 2020."),
        "format": "TSV",
    },
}


def example_data(name=None):
    """Access bundled example datasets.

    This function provides access to example phylogenetic trees and metadata
    from published studies for use in tutorials, testing, and examples.

    Args:
        name: Name of the dataset (filename without extension).
            If None, displays a listing of all available datasets and
            returns None.

    Returns:
        pathlib.Path: Path to the requested dataset file if name is valid.
        None: If name is None or invalid, prints message and returns None.

    Examples:
        >>> from heattree_py import example_data, heat_tree
        >>>
        >>> # Show all available datasets
        >>> example_data()
        >>>
        >>> # Get path to a specific dataset
        >>> tree_path = example_data("bansal_2021_tree")
        >>> metadata_path = example_data("bansal_2021_metadata")
        >>>
        >>> # Use directly with heat_tree
        >>> heat_tree(tree_path, metadata=metadata_path)
    """
    if name is not None and name not in _DATASET_INFO:
        print(f"Unknown dataset: {name!r}\n")

    if name is None or name not in _DATASET_INFO:
        print("Available datasets:\n")
        for dataset_name in sorted(_DATASET_INFO.keys()):
            info = _DATASET_INFO[dataset_name]
            print(f"- {dataset_name} ({info['format']}): {info['description']}\n")
        return None

    filename = _DATASET_INFO[name]["filename"]
    path = _DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    return path
