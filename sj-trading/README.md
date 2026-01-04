# sj-trading

Stock trading application using Shioaji API (永豐金證券)

## Installation

```bash
pip install -e ".[dev]"
```

## Development

This project uses the following development tools:

- **ruff**: Fast Python linter and formatter
- **mypy**: Static type checker
- **pytest**: Testing framework
- **pre-commit**: Git hooks for code quality

### Setup pre-commit hooks

```bash
pre-commit install
```

### Run linting and formatting

```bash
ruff check .
ruff format .
```

### Run type checking

```bash
mypy .
```

### Run tests

```bash
pytest
```
