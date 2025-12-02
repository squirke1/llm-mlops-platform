# CI/CD Pipeline

Automated testing, building, and deployment using GitHub Actions.

## 🔄 Workflows

### 1. **CI Pipeline** (`ci.yml`)
**Triggers**: Every PR and push to `develop`/`main`

Runs complete validation:
- ✅ **Linting**: black, flake8, isort checks
- ✅ **Tests**: pytest with 22 unit tests
- ✅ **Docker Build**: Validates Dockerfile builds
- ✅ **K8s Validation**: Checks Kubernetes manifest syntax
- ✅ **Terraform Validation**: Validates IaC configuration

### 2. **Test Workflow** (`test.yml`)
**Triggers**: PR, push, manual

- Runs all pytest tests
- Generates coverage reports
- Uploads to Codecov (optional)
- Matrix testing with Python 3.9

### 3. **Lint Workflow** (`lint.yml`)
**Triggers**: PR, push, manual

Code quality checks:
- `black --check` - Code formatting
- `isort --check` - Import sorting
- `flake8` - PEP8 compliance
- `mypy` - Type checking (non-blocking)

### 4. **Docker Workflow** (`docker.yml`)
**Triggers**: PR, push, manual

- Builds Docker image with buildx
- Uses layer caching for speed
- Tests image imports work correctly
- Tags with commit SHA

### 5. **Deploy Workflow** (`deploy.yml`)
**Triggers**: Push to `main`, manual

Production deployment (currently disabled):
- Login to AWS ECR
- Build and push Docker image
- Update kubeconfig for EKS
- Deploy to Kubernetes cluster
- Verify deployment status

**Note**: Deployment is disabled (`if: false`) until AWS credentials are configured.

## 📊 Status Badges

Add these to your README.md:

```markdown
![CI Pipeline](https://github.com/squirke1/llm-mlops-platform/actions/workflows/ci.yml/badge.svg)
![Tests](https://github.com/squirke1/llm-mlops-platform/actions/workflows/test.yml/badge.svg)
![Docker Build](https://github.com/squirke1/llm-mlops-platform/actions/workflows/docker.yml/badge.svg)
```

## 🚀 How It Works

### On Pull Request:
```
Developer pushes code
     ↓
GitHub Actions triggered
     ↓
┌─────────────────────┐
│  1. Lint Check      │ → black, flake8, isort
├─────────────────────┤
│  2. Run Tests       │ → pytest (22 tests)
├─────────────────────┤
│  3. Build Docker    │ → Validate Dockerfile
├─────────────────────┤
│  4. Validate K8s    │ → kubectl dry-run
├─────────────────────┤
│  5. Validate TF     │ → terraform validate
└─────────────────────┘
     ↓
All green? → ✅ Ready to merge
Any red? → ❌ Fix and push again
```

### On Merge to Main:
```
Code merged to main
     ↓
Deploy workflow triggered (when enabled)
     ↓
1. Build Docker image → Push to ECR
2. Update kubeconfig → Connect to EKS
3. Apply K8s manifests → Deploy pods
4. Verify deployment → Check pod status
     ↓
✅ Production updated
```

## 🛠️ Local Testing

### Run Tests Locally
```bash
# All tests
make test

# With coverage
pytest tests/ --cov=src --cov=api --cov-report=term-missing
```

### Run Linters Locally
```bash
# Check formatting
make lint

# Auto-fix formatting
black src/ api/ tests/
isort src/ api/ tests/
```

### Test Docker Build
```bash
# Build image
docker build -t churn-prediction-api:test .

# Test image works
docker run --rm churn-prediction-api:test python -c "import src.model; print('OK')"
```

### Validate Kubernetes
```bash
# Dry-run validation
kubectl apply --dry-run=client -k k8s/
```

### Validate Terraform
```bash
cd terraform/
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

## ⚙️ Configuration

### GitHub Secrets (for AWS deployment)
Add these in: Settings → Secrets and variables → Actions

Required secrets:
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

### Enable AWS Deployment
1. Add AWS credentials to GitHub Secrets
2. Deploy infrastructure: `terraform apply`
3. Edit `.github/workflows/deploy.yml`
4. Remove `if: false` from deployment steps
5. Push to `main` branch

## 🎯 Key Features

### Parallel Execution
Workflows run simultaneously for faster feedback:
- Lint + Test run in parallel
- Docker build waits for both to pass
- Total CI time: ~3-5 minutes

### Caching
- Pip dependencies cached between runs
- Docker layers cached for faster builds
- Terraform providers cached

### Matrix Testing
Test workflow supports multiple Python versions:
```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11"]
```

### Manual Triggers
All workflows support `workflow_dispatch` for manual runs:
- Go to Actions tab
- Select workflow
- Click "Run workflow"

## 📈 Monitoring

### View Workflow Runs
```bash
# Via GitHub CLI
gh run list
gh run view <run-id>
gh run watch

# Or visit
https://github.com/squirke1/llm-mlops-platform/actions
```

### Check PR Status
Every PR shows status checks:
- ✅ All checks passed → Safe to merge
- ⏳ Checks running → Wait
- ❌ Checks failed → Click "Details" to debug

## 🐛 Debugging Failed Workflows

### Common Issues

**1. Tests Failing**
```bash
# Run locally first
pytest tests/ -v

# Check specific test
pytest tests/test_api.py::test_predict_valid_request -v
```

**2. Linting Errors**
```bash
# Auto-fix formatting
black src/ api/ tests/
isort src/ api/ tests/

# Check remaining issues
flake8 src/ api/ tests/
```

**3. Docker Build Fails**
```bash
# Test locally
docker build -t test .

# Check syntax
docker build --check .
```

**4. Kubernetes Validation Fails**
```bash
# Validate YAML
kubectl apply --dry-run=client -f k8s/deployment.yaml

# Check syntax
yamllint k8s/
```

## 🎤 Interview Talking Points

1. **Automated Testing**: Every PR runs 22 tests automatically
2. **Code Quality**: Black, flake8, isort enforce consistent style
3. **Docker Validation**: Builds tested in CI before merging
4. **Infrastructure Validation**: Terraform and K8s checked on every change
5. **Fast Feedback**: Parallel jobs complete in 3-5 minutes
6. **Caching**: Dependencies cached for 10x faster builds
7. **Security**: AWS credentials stored as encrypted secrets
8. **GitOps**: Infrastructure changes go through same CI as code
9. **Deployment Safety**: Manual approval gates (can be added)
10. **Observability**: Status badges show build health at a glance

## 📚 GitHub Actions Concepts

### Workflows
YAML files in `.github/workflows/` that define automation

### Jobs
Separate units of work that run in parallel (unless `needs:` specified)

### Steps
Individual commands within a job (run sequentially)

### Runners
GitHub-hosted Ubuntu VMs that execute workflows (free for public repos)

### Triggers
Events that start workflows: `push`, `pull_request`, `workflow_dispatch`

### Secrets
Encrypted environment variables for sensitive data (API keys, credentials)

### Matrix
Run same job with different configurations (multiple Python versions)

### Caching
Store dependencies between runs to speed up workflows

## 🔒 Security Best Practices

✅ Never commit AWS credentials
✅ Use GitHub Secrets for sensitive data
✅ Enable branch protection rules
✅ Require status checks before merge
✅ Use least-privilege IAM roles
✅ Scan Docker images for vulnerabilities
✅ Pin action versions (e.g., `@v4` not `@latest`)

## 📊 Free Tier Limits

GitHub Actions free for public repos:
- ✅ Unlimited minutes
- ✅ Unlimited storage
- ✅ 20 concurrent jobs

For private repos:
- 2,000 minutes/month
- 500 MB storage
- Charges after limit

## 🚦 Next Steps

After Phase 7:
1. **Phase 8**: Add Prometheus & Grafana monitoring
2. **Phase 9**: MLflow for experiment tracking
3. **Phase 10**: Production hardening (secrets, monitoring alerts)

## 💡 Cost Considerations

**Current Setup (Free)**:
- GitHub Actions: $0 (public repo)
- Testing in CI: $0 (GitHub runners)
- Docker Hub: $0 (public images)

**If Deploying to AWS**:
- Would trigger deploy workflow
- Costs ~$200/month for EKS infrastructure
- Can disable by keeping `if: false` in deploy.yml
