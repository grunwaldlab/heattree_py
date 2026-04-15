# Development Guide

This document describes the development environment, tools, and workflows for contributing to this project.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/grunwaldlab/heattree_py.git
cd heattree_py

# Install hatch (if not already installed)
pip install hatch

# Run tests
hatch run test

# Run all quality checks
hatch run all
```

## Development Environment

This project uses [**Hatch**](https://hatch.pypa.io/) as its project manager and build backend. Hatch handles:

- Virtual environment management
- Dependency installation
- Build and packaging
- Task running (scripts)
- Version management

### Installing Hatch

```bash
pip install hatch
# or with pipx (recommended for tools)
pipx install hatch
```

### Environment Setup

Hatch automatically creates and manages virtual environments. No manual `venv` or `pip install` needed:

```bash
# The default environment is created automatically on first use
hatch run python --version

# Run commands in the default environment
hatch run pytest

# Enter an interactive shell in the environment
hatch shell
```

## Tool Overview

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Hatch** | Project manager, build backend, task runner | `pyproject.toml` `[tool.hatch]` |
| **Ruff** | Linting and code formatting | `pyproject.toml` `[tool.ruff]` |
| **Pytest** | Testing framework | `pyproject.toml` `[tool.pytest.ini_options]` |


## Common Tasks

All tasks are run through Hatch scripts defined in `pyproject.toml`:

### Testing

```bash
# Run all tests
hatch run test

# Run specific test file
hatch run test tests/test_core.py

# Run specific test function
hatch run test tests/test_core.py::test_function_name

# Run with additional pytest arguments
hatch run test -xvs tests/test_core.py
```

### Code Quality

```bash
# Run linter
hatch run lint

# Format code
hatch run format

# Auto-fix linting issues
hatch run fix

# Run all quality checks (lint + test)
hatch run all
```

### Documentation

```bash
# Serve docs locally
hatch run docs:serve

# Build documentation
hatch run docs:build

# Deploy to GitHub Pages
hatch run docs:deploy
```

### Manual Tool Usage

If you prefer running tools directly (requires `hatch shell` first):

```bash
# Enter the environment
hatch shell

# Run individual tools
ruff check src tests
ruff format src tests
ruff check --fix src tests
pytest
```


### Key Design Decisions

- **src/ layout**: Separates source code from tests and docs
   - Prevents importing from the working directory
   - Ensures tests run against the installed package

- **Single pyproject.toml**: All tool configurations in one place
   - No separate `.flake8`, `setup.cfg`, `setup.py`, or `tox.ini`
   - Modern PEP 518/621 standard

- **Hatch environments**: Isolated environments per purpose
   - `default`: Development (tests, linting)
   - `docs`: Documentation building
   - Easy to add more (e.g., `lint` for CI)

## Writing Tests

### Test File Structure

```python
# tests/test_widget.py
import pandas as pd
import pytest

from heattree_py._widget import _to_newick, heat_tree


SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"


class TestToNewick:
    """Tests for the _to_newick helper."""

    def test_newick_string(self):
        """A plain Newick string is returned as-is."""
        assert _to_newick(SIMPLE_NEWICK) == SIMPLE_NEWICK

    def test_file_path(self, tmp_path):
        """A file path to a Newick file is read correctly."""
        f = tmp_path / "tree.nwk"
        f.write_text(SIMPLE_NEWICK)
        assert _to_newick(str(f)) == SIMPLE_NEWICK


class TestHeatTree:
    """Integration tests for the public heat_tree function."""

    def test_simple_tree(self):
        """A Newick string produces a widget with an iframe."""
        html = heat_tree(SIMPLE_NEWICK).to_html()
        assert "<iframe" in html

    def test_with_metadata(self):
        """Metadata and aesthetics are embedded in the widget."""
        meta = pd.DataFrame({
            "node_id": ["A", "B", "C", "D"],
            "group": ["x", "x", "y", "y"],
        })
        html = heat_tree(
            SIMPLE_NEWICK,
            metadata=meta,
            aesthetics={"tipLabelColor": "group"},
        ).to_html()
        assert "tipLabelColor" in html
```

### Running Tests

```bash
# Run all tests
hatch run test

# Run with verbose output
hatch run test -v

# Run specific marker
hatch run test -m "slow"

# Skip slow tests
hatch run test -m "not slow"

# Run in parallel (using pytest-xdist)
hatch run test -n auto

# Stop on first failure
hatch run test -x
```

## Code Style

### General Guidelines

1. **Follow PEP 8**: Enforced by Ruff
2. **Write docstrings**: Google style (enforced by Ruff)
3. **Maximum line length**: 88 characters (Black-compatible)

### Import Style

Ruff automatically sorts and formats imports:

```python
# Standard library
import json
from pathlib import Path

# Third-party
import pandas as pd

# First-party (this package)
from heattree_py import heat_tree
from heattree_py._widget import _to_newick
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_total(items, tax_rate=0.0):
    """Calculate the total cost of items including tax.

    Args:
        items: List of items to purchase.
        tax_rate: Sales tax rate as a decimal (e.g., 0.08 for 8%).

    Returns:
        Total cost including tax.

    Raises:
        ValueError: If tax_rate is negative.

    Example:
        >>> items = [Item(price=10.0), Item(price=20.0)]
        >>> calculate_total(items, tax_rate=0.08)
        32.4
    """
    if tax_rate < 0:
        raise ValueError("tax_rate cannot be negative")
    ...
```

## Troubleshooting

### Environment Issues

```bash
# Reset the environment
hatch env prune

# Recreate and install dependencies
hatch run python --version
```

### Test Discovery Issues

```bash
# See collected tests without running
hatch run test --collect-only

# Run with full traceback
hatch run test --tb=long
```

## Additional Resources

- [Hatch Documentation](https://hatch.pypa.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)
