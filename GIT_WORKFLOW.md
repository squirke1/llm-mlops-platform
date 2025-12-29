# Git Workflow Guide

## Branch Strategy

We use a simplified Git Flow approach suitable for solo/small team projects:

```
main (production-ready code)
   develop (integration branch)
       feature/churn-model
       feature/api-endpoint
       feature/docker-setup
   hotfix/critical-bug
```

## Branch Types

### `main`
- **Production-ready** code only
- All code here should be deployable
- Protected branch (no direct commits)
- Tagged with version numbers (v1.0.0, v1.1.0)

### `develop`
- **Integration branch** for features
- Latest development changes
- Should always be in a working state
- Base branch for all feature branches

### `feature/*`
- New features or enhancements
- Branch from: `develop`
- Merge back to: `develop`
- Naming: `feature/short-description`
- Examples: `feature/ml-model`, `feature/api-endpoint`

### `bugfix/*`
- Non-critical bug fixes
- Branch from: `develop`
- Merge back to: `develop`
- Naming: `bugfix/issue-description`

### `hotfix/*`
- Critical production fixes
- Branch from: `main`
- Merge to: `main` AND `develop`
- Naming: `hotfix/critical-issue`

## Daily Workflow

### Starting New Work

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on your feature...
# Make small, focused commits
git add .
git commit -m "feat: add customer churn model"
```

### Committing Changes

Use **conventional commits** format:

```bash
# Format: <type>: <description>

git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in data preprocessing"
git commit -m "docs: update README with setup instructions"
git commit -m "test: add unit tests for model"
git commit -m "refactor: improve code structure"
git commit -m "chore: update dependencies"
```

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks
- `style:` - Code style changes (formatting)
- `perf:` - Performance improvements

### Merging Back to Develop

```bash
# Ensure your branch is up to date
git checkout develop
git pull origin develop
git checkout feature/your-feature
git merge develop  # Resolve any conflicts

# Run tests before merging
make test
make lint

# Merge to develop
git checkout develop
git merge feature/your-feature --no-ff
git push origin develop

# Delete feature branch (optional)
git branch -d feature/your-feature
```

### Releasing to Main

```bash
# When develop is stable and ready for release
git checkout main
git pull origin main
git merge develop --no-ff
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
```

## Quick Reference

### Current Phase Work (Phase 1: ML Model)

```bash
# Create feature branch for Phase 1
git checkout -b feature/phase-1-ml-model

# Make changes, commit frequently
git add src/data.py
git commit -m "feat: add sample data generation"

git add src/model.py
git commit -m "feat: implement random forest classifier"

git add tests/test_model.py
git commit -m "test: add model unit tests"

# When phase complete, merge to develop
git checkout develop
git merge feature/phase-1-ml-model --no-ff
git push origin develop
```

## Best Practices

1. **Commit early and often** - Small, atomic commits
2. **Write meaningful commit messages** - Use conventional format
3. **Pull before push** - Always sync with remote first
4. **Test before merging** - Run `make test` and `make lint`
5. **Keep branches short-lived** - Merge features within days, not weeks
6. **Never commit to main directly** - Always use pull requests or merge from develop
7. **Clean up branches** - Delete merged feature branches

## For This Project

Since we're building incrementally (Phase 1, 2, 3...), suggested approach:

```bash
# Option 1: Feature branch per phase (recommended for learning)
feature/phase-1-ml-model
feature/phase-2-data-pipeline
feature/phase-3-enhanced-training
# etc.

# Option 2: Smaller feature branches within phases
feature/data-generation
feature/model-training
feature/model-evaluation
```

## Setup Commands

```bash
# Create develop branch (one-time setup)
git checkout -b develop
git push -u origin develop

# Set default branch to develop for new work
git config branch.develop.remote origin
git config branch.develop.merge refs/heads/develop
```

## Emergency: Undoing Changes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Discard uncommitted changes
git checkout -- <file>

# Stash changes temporarily
git stash
git stash pop  # Restore later
```

---

**Next Step**: Set up the develop branch and create your first feature branch for Phase 1!
