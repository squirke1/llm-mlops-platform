# Setup Instructions

## Quick Start

```bash
# 1. Clone the repository (if not already done)
git clone https://github.com/squirke1/llm-mlops-platform.git
cd llm-mlops-platform

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# 3. Install dependencies
make install

# 4. Verify setup
python --version  # Should show Python 3.10+
make format      # Should run without errors
```

## What's Included

### Project Structure
```
llm-mlops-platform/
 src/              # Source code
 tests/            # Unit tests
 data/             # Data files (gitignored)
    raw/         # Raw data
    processed/   # Processed data
 models/           # Trained models (gitignored)
 notebooks/        # Jupyter notebooks for exploration
 scripts/          # Utility scripts
 docs/             # Documentation
 requirements.txt  # Python dependencies
 pyproject.toml   # Tool configurations
 Makefile         # Common commands
 .flake8          # Linting configuration
```

### Development Tools
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Code linting
- **mypy**: Type checking
- **pytest**: Testing framework

## Development Workflow

### Before coding
```bash
source venv/bin/activate
```

### While coding
```bash
# Format your code
make format

# Run linting
make lint

# Run tests
make test
```

### Committing
```bash
make format        # Format before committing
git add .
git commit -m "type: description"
```

## Next Steps

Phase 0 is complete! Now you can:
1.  Start writing code in `src/`
2.  Add tests in `tests/`
3.  Use `make` commands for common tasks

See `PHASE_0.md` for details, then move to Phase 1.
