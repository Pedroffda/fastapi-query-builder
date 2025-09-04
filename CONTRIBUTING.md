# Contributing to FastAPI Query Builder

Thank you for your interest in contributing to FastAPI Query Builder! This document provides guidelines and information for contributors.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots and animated GIFs if possible**
- **Include the version of Python, FastAPI, SQLAlchemy, and the library you're using**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**
- **List some other applications where this enhancement exists**

### Pull Requests

- Fill in the required template
- Do not include issue numbers in the PR title
- Include screenshots and animated GIFs in your pull request whenever possible
- Follow the Python style guide (PEP 8)
- Include thoughtfully-worded, well-structured tests
- Document new code based on the Documentation Guidelines
- End all files with a newline

## Development Setup

### Prerequisites

- Python 3.8+
- pip
- git

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/Pedroffda/fastapi-query-builder.git
   cd fastapi-query-builder
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .[dev]
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=query_builder --cov-report=html

# Run specific test file
pytest tests/test_filter_parser.py

# Run tests with verbose output
pytest -v
```

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run all checks:
```bash
black .
isort .
flake8 .
mypy .
```

### Documentation

- Use docstrings for all public functions and classes
- Follow Google style docstrings
- Update README.md if adding new features
- Add examples for new functionality

## Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Examples

```
feat(filter): add support for date range filtering
fix(mapper): resolve circular reference issue
docs: update installation instructions
test: add integration tests for search functionality
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a release branch
4. Run full test suite
5. Create pull request
6. After approval, merge to main
7. Create GitHub release
8. Package is automatically published to PyPI

## Questions?

If you have questions about contributing, please:

1. Check existing issues and discussions
2. Create a new issue with the "question" label
3. Join our community discussions

Thank you for contributing to FastAPI Query Builder!
