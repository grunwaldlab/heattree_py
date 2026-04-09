# Contributing to MyPackage

Thank you for your interest in contributing to MyPackage! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [Hatch](https://hatch.pypa.io/) (install with `pip install hatch`)

### Setting Up Your Development Environment

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/heattree_py.git
   cd heattree_py
   ```
3. Check [docs/development.md](docs/development.md) for tools and conventions used for this software

## Making Changes

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/my-feature
   # or
   git checkout -b fix/my-bugfix
   ```

2. Make your changes and ensure tests pass:
   ```bash
   hatch run all
   ```

3. Commit your changes with a clear message:
   ```bash
   git commit -m "feat: add new feature"
   ```

- Add entries to `CHANGELOG.md` for notable changes

## Submitting Changes

1. **Push your branch**:
   ```bash
   git push origin feature/my-feature
   ```

2. **Create a Pull Request** on GitHub
   - Link any related issues
   - Ensure all CI checks pass

## Pull Request Checklist

Before submitting, ensure:

- [ ] Tests pass locally (`hatch run test`)
- [ ] Code is formatted (`hatch run format`)
- [ ] No linting errors (`hatch run lint`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)

## Questions?

- Open an issue for questions or problems
- Join discussions in existing issues and PRs
