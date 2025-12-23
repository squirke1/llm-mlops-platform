# Phase 0: Project Foundation Setup

##  Goal
Set up a professional project foundation following industry best practices.

##  What Experienced Developers Do First

Before writing any code, they:
1. **Plan the architecture** - Know what you're building
2. **Set up version control** - Git configuration
3. **Define dependencies** - Lock versions early
4. **Structure the project** - Follow conventions
5. **Configure tools** - Linters, formatters, type checkers
6. **Write documentation** - README, contributing guides

##  Tasks

### 1. Project Structure (5 min)
```bash
# Create standard Python project layout
mkdir -p src tests docs data/{raw,processed} models notebooks scripts
touch src/__init__.py tests/__init__.py
```

**Why?** Standard structure makes the project immediately recognizable to other developers.

### 2. Python Environment (5 min)
```bash
# Use Python 3.10+ for modern features
python3 --version  # Should be 3.10 or higher

# Create isolated virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip to latest
pip install --upgrade pip
```

**Why?** Virtual environments prevent dependency conflicts and ensure reproducibility.

### 3. Dependencies with Version Pinning (5 min)
Create `requirements.txt` with **exact versions** (not ranges):
```txt
# Core ML
scikit-learn==1.3.2
pandas==2.1.4
numpy==1.26.2
joblib==1.3.2

# Development
pytest==7.4.4
black==23.12.1
flake8==7.0.0
isort==5.13.2
```

**Why?** Pinned versions ensure reproducible builds and prevent "it works on my machine" issues.

### 4. Git Configuration (2 min)
```bash
# Ensure proper .gitignore
# Check data/ and models/ are ignored

# Make initial commit
git add .
git commit -m "chore: initialize project structure"
```

**Why?** Good Git hygiene from day one prevents issues later.

### 5. Code Quality Tools Setup (10 min)
Create `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

**Why?** Automated formatting and linting save hours of code review time.

### 6. Development Workflow (3 min)
Create `Makefile` for common tasks:
```makefile
.PHONY: install test format lint

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
```

**Why?** Standardized commands make onboarding new developers easier.

##  Completion Checklist

- [ ] Project directories created
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Tools configured (black, flake8, pytest)
- [ ] Initial Git commit made
- [ ] Can run `make format` successfully

##  Professional Tips

1. **Don't skip setup** - A solid foundation saves hours later
2. **Document as you go** - Future you will thank you
3. **Use make/scripts** - Automate repetitive tasks
4. **Test the setup** - Make sure others can replicate it
5. **Commit early, commit often** - Small, atomic commits

##  Next Steps

Once Phase 0 is complete, you'll have:
-  Professional project structure
-  Reproducible environment
-  Quality tools configured
-  Ready to write code

**Move to Phase 1**: Build the first ML model with proper structure.

---

##  Commands Summary

```bash
# Complete Phase 0 setup
mkdir -p src tests docs data/{raw,processed} models notebooks scripts
touch src/__init__.py tests/__init__.py
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
make format
git add .
git commit -m "chore: complete phase 0 setup"
```
