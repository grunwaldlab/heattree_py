# heattree_py

Interactive phylogenetic tree visualisation for Jupyter notebooks.

`heattree-py` embeds the JavaScript [heat-tree](https://github.com/grunwaldlab/heat-tree)
widget into Jupyter notebooks using `IPython.display.HTML`. The output is fully
self-contained and works in live Jupyter sessions **and** in offline HTML exports
(no running Python kernel required).

This is the Python counterpart of the R [heattree](https://github.com/grunwaldlab/heattree)
package.

## Installation

```bash
pip install heattree_py
```

## Documentation

Full documentation with interactive examples is available at:
**https://grunwaldlab.github.io/heattree_py/**

## Quick start

```python
from heattree_py import heat_tree

# Minimal example with a Newick string
heat_tree("(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);")
```

## Usage

### Tree input

`heat_tree()` accepts trees in any of the common Python formats:

```python
# Newick string
heat_tree("(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);")

# Path to a Newick file
heat_tree("path/to/tree.nwk")

# ete3 TreeNode
from ete3 import Tree
tree = Tree("(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);")
heat_tree(tree)

# dendropy Tree
import dendropy
tree = dendropy.Tree.get(data="(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);", schema="newick")
heat_tree(tree)

# Biopython Phylo tree
from Bio import Phylo
from io import StringIO
tree = Phylo.read(StringIO("(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"), "newick")
heat_tree(tree)

# scikit-bio TreeNode
import skbio
tree = skbio.TreeNode.read(StringIO("(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"))
heat_tree(tree)
```

### Metadata

Pass a `pandas.DataFrame` to colour or size tree elements by metadata
columns. The DataFrame must include a column whose values match node labels in
the tree (the JavaScript widget detects the matching column automatically).

```python
import pandas as pd
from heattree_py import heat_tree

tree = "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"

metadata = pd.DataFrame({
    "node_id": ["A", "B", "C", "D"],
    "group":   ["x", "x", "y", "y"],
    "size":    [10, 20, 30, 40],
})

heat_tree(tree, metadata=metadata, aesthetics={"tipLabelColor": "group"})
```

If the DataFrame index contains node IDs (rather than a column), it is
automatically included as a column and used for matching:

```python
metadata = pd.DataFrame(
    {"group": ["x", "x", "y", "y"]},
    index=["A", "B", "C", "D"],
)
heat_tree(tree, metadata=metadata, aesthetics={"tipLabelColor": "group"})
```

File paths to TSV/CSV files are also accepted:

```python
heat_tree("tree.nwk", metadata="metadata.tsv")
```

### Aesthetics

The `aesthetics` parameter maps visual properties to metadata columns:

| Aesthetic         | Description                        | Data type              |
|-------------------|------------------------------------|------------------------|
| `tipLabelText`    | Text content of tip labels         | any                    |
| `tipLabelColor`   | Colour of tip labels               | categorical/continuous |
| `tipLabelSize`    | Size of tip labels                 | continuous             |
| `tipLabelFont`    | Font family for tip labels         | categorical            |
| `tipLabelStyle`   | Font style (normal, bold, italic)  | categorical            |

```python
heat_tree(
    tree,
    metadata=metadata,
    aesthetics={
        "tipLabelColor": "group",
        "tipLabelSize": "size",
    },
)
```

### Widget options

Additional keyword arguments are forwarded to the JavaScript widget as
configuration options:

```python
heat_tree(
    tree,
    layout="circular",          # "rectangular" (default) or "circular"
    branchLengthScale=1.5,      # scale factor for branch lengths
    treeHeightScale=2.0,        # scale factor for spacing between tips
    transitionDuration=750,     # animation duration in ms
)
```

See the [heat-tree documentation](https://github.com/grunwaldlab/heat-tree)
for the full list of options.

### Multiple trees

Pass a list of trees (and optionally matching lists of metadata and
aesthetics) to initialise the widget with multiple trees:

```python
heat_tree(
    tree=["(A,B,(C,D));", "(E,F,(G,H));"],
    metadata=[meta1, meta2],
    aesthetics=[{"tipLabelColor": "group"}, None],
)
```

### Widget sizing

```python
heat_tree(tree, width="80%", height="600px")
```

## How it works

`heat_tree()` generates a self-contained HTML document that loads the
[`@grunwaldlab/heat-tree`](https://www.npmjs.com/package/@grunwaldlab/heat-tree)
JavaScript library from a CDN and initialises the interactive widget. This
document is embedded in an `<iframe>` and returned as an
`IPython.display.HTML` object. The iframe approach ensures the JavaScript
executes correctly across all Jupyter front-ends (classic Notebook, JupyterLab,
VS Code, Google Colab) and in static HTML exports.

## Development

```bash
pip install hatch

# Run all checks (lint + test)
hatch run all

# Run tests only
hatch run test

# Auto-fix lint/format issues
hatch run fix
```

## License

MIT
