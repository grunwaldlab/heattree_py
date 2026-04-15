# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Quick Reference

```bash
# Run all quality checks
hatch run all

# Run tests
hatch run test
hatch run test tests/test_core.py::TestAdd::test_add_positive_integers

# Fix code issues
hatch run fix
```

## Tools Used

| Tool | Purpose | Command |
|------|---------|---------|
| **hatch** | Project manager, env manager, task runner | `hatch run <script>` |
| **ruff** | Linting and formatting | `hatch run lint`, `hatch run format` |
| **pytest** | Testing | `hatch run test` |

## Code Style

1. **Google-style docstrings** for all public functions
2. **Line length**: 88 characters (Black-compatible)
3. **Import sorting**: Automatic via ruff
4. **Naming**:
   - modules: `lowercase`
   - classes: `PascalCase`
   - functions/vars: `snake_case`
   - constants: `UPPER_SNAKE_CASE`

## Coding conventions

- Complexity is a liability and should only be introduced when it has significant benefits.
- Dont write short wrapper functions for other functions.
- Only check types and parameter validity on public APIs.


## Testing conventions

- Dont write trivial tests; no tests for the sake of tests.
- Only test public APIs.
- Dont design tests to pass, design tests that test what the user expects to happen or fail.
- This pacakge primarily embeds JS widgets. The effect they have on the dom should be tested with playwright

## Before Submitting Changes

Always run:
```bash
hatch run all
```

This runs: lint + test

## Configuration Locations

All tool configs are in `pyproject.toml`:
- `[tool.hatch.*]` - Hatch configuration
- `[tool.ruff]` - Ruff linting/formatting rules
- `[tool.pytest.ini_options]` - Test configuration

## When to edit CHANGELOG.md

Only add to CHANGELOG.md when a feature changes how users will experience the software, such as added features, changes to public API, or significant performance increases.
Do not mention things only of interest to developers, such as refactoring.
