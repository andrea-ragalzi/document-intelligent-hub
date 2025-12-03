# Quality Gate Setup

This document describes the comprehensive Quality Gate (QG) implementation for the Document Intelligent Hub monorepo.

## Overview

The Quality Gate enforces strict code quality, type safety, and testing standards across both Backend (Python/FastAPI) and Frontend (TypeScript/Next.js) codebases through automated CI/CD checks and local VS Code integration.

## Quality Triplets

### Backend QG Triplet (Python/FastAPI)

| Tool       | Role                     | Standard Enforcement                                             | QG Condition          |
| ---------- | ------------------------ | ---------------------------------------------------------------- | --------------------- |
| **Pylint** | Quality & Style Checker  | Enforces PEP 8. Complexity checks disabled (delegated to Lizard) | Score ≥ 9.0/10        |
| **Mypy**   | Type Checker             | Strict type checking (`--strict` mode)                           | Zero type errors      |
| **Lizard** | Complexity Metric        | Measures Cyclomatic Complexity (CCN)                             | CCN ≤ 15 per function |
| **Pytest** | Unit/Integration Testing | Executes tests with coverage reporting                           | Coverage ≥ 80%        |

### Frontend QG Triplet (TypeScript/Next.js)

| Tool           | Role                    | Standard Enforcement                            | QG Condition                  |
| -------------- | ----------------------- | ----------------------------------------------- | ----------------------------- |
| **ESLint**     | Quality & Style Checker | Enforces TypeScript, React Hooks, Next.js rules | Zero errors/warnings          |
| **TypeScript** | Type Checker            | Strict type checking during compilation         | Zero compilation errors       |
| **Prettier**   | Formatter               | Ensures uniform code style                      | Formatting consistency passed |
| **Vitest**     | Unit/Component Testing  | Executes tests with coverage reporting          | Coverage ≥ 80%                |

## CI/CD Pipeline

### GitHub Actions Workflow

The Quality Gate workflow (`.github/workflows/quality-gate.yml`) runs on every push to branches except `main`:

**Backend Checks:**

1. Pylint with minimum score of 9.0/10 (complexity checks disabled)
2. Mypy strict type checking
3. Lizard complexity check (CCN ≤ 15)
4. Pytest with 80% minimum coverage

**Frontend Checks:**

1. ESLint with zero warnings
2. TypeScript type check
3. Prettier format verification
4. Vitest with 80% minimum coverage

**Workflow Behavior:**

- Runs in parallel for backend and frontend
- Fails the build if any check doesn't meet QG conditions
- Uploads coverage reports to Codecov
- Provides summary job showing overall status

### Branch Protection

Configure branch protection rules in GitHub:

- Require status checks to pass before merging
- Require `backend-quality-gate` and `frontend-quality-gate` to pass
- Enforce for administrators

## Local Development Setup

### Backend (Python)

**Installation:**

```bash
cd backend
poetry install
```

**Configuration Files:**

- `.pylintrc` - Pylint configuration (PEP 8, complexity checks disabled)
- `mypy.ini` - Mypy strict type checking configuration
- `pytest.ini` - Pytest and coverage settings
- `.vscode/settings.json` - VS Code Pylance strict mode (local development)

**Manual Quality Checks:**

```bash
# Run Pylint
poetry run pylint app/ --rcfile=.pylintrc

# Run Mypy type checking
poetry run mypy app/ --strict

# Run Lizard complexity check
poetry run lizard app/ -l python -C 15 -w

# Run tests with coverage
poetry run pytest --cov=app --cov-report=term --cov-fail-under=80
```

**VS Code Integration:**

- Pylance strict type checking enabled (local development)
- Pylint runs on save
- Mypy integration via Python extension
- 120-character ruler displayed
- Auto-organize imports on save

### Frontend (TypeScript/Next.js)

**Installation:**

```bash
cd frontend
npm install
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
```

**Configuration Files:**

- `eslint.config.mjs` - ESLint rules
- `.prettierrc` - Prettier formatting rules
- `.prettierignore` - Files to exclude from formatting
- `tsconfig.json` - TypeScript strict mode configuration

**Manual Quality Checks:**

```bash
# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix

# Check formatting
npm run format:check

# Format code
npm run format

# Type check
npm run type-check

# Run tests with coverage
npm run test:coverage

# Run all checks
npm run quality:check
```

**VS Code Integration:**

- ESLint auto-fix on save
- Prettier format on save
- TypeScript workspace version used
- 100-character ruler displayed

## Pre-commit Hooks (Recommended)

Install `pre-commit` to run quality checks before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

Create `.pre-commit-config.yaml` in repository root:

```yaml
repos:
  - repo: local
    hooks:
      # Backend hooks
      - id: pylint-backend
        name: Pylint (Backend)
        entry: bash -c 'cd backend && poetry run pylint app/'
        language: system
        types: [python]
        pass_filenames: false

      - id: lizard-backend
        name: Lizard Complexity (Backend)
        entry: bash -c 'cd backend && poetry run lizard app/ -C 15'
        language: system
        types: [python]
        pass_filenames: false

      # Frontend hooks
      - id: eslint-frontend
        name: ESLint (Frontend)
        entry: bash -c 'cd frontend && npm run lint'
        language: system
        types: [ts, tsx, javascript, jsx]
        pass_filenames: false

      - id: prettier-frontend
        name: Prettier (Frontend)
        entry: bash -c 'cd frontend && npm run format:check'
        language: system
        types: [ts, tsx, javascript, jsx, json, css, markdown]
        pass_filenames: false

      - id: typescript-frontend
        name: TypeScript Check (Frontend)
        entry: bash -c 'cd frontend && npm run type-check'
        language: system
        types: [ts, tsx]
        pass_filenames: false
```

## Troubleshooting

### Backend Issues

**Pylint score too low:**

- Review Pylint output for specific violations
- Focus on critical errors (E) and warnings (W) first
- Refactor code to follow PEP 8 guidelines
- Update `.pylintrc` to disable specific checks if justified

**High complexity (CCN > 15):**

- Break down large functions into smaller ones
- Extract complex logic into helper functions
- Use early returns to reduce nesting

**Low test coverage:**

- Write tests for untested code paths
- Focus on critical business logic first
- Use `pytest --cov=app --cov-report=html` to identify gaps

### Frontend Issues

**ESLint errors:**

- Run `npm run lint:fix` to auto-fix issues
- Review React Hooks exhaustive-deps warnings carefully
- Update ESLint configuration if rules are too strict

**Prettier formatting:**

- Run `npm run format` to auto-format all files
- Ensure VS Code Prettier extension is installed
- Check `.prettierignore` if files shouldn't be formatted

**TypeScript errors:**

- Enable strict mode gradually if migrating old code
- Use proper type annotations instead of `any`
- Leverage VS Code IntelliSense for type suggestions

**Low test coverage:**

- Write unit tests for utilities and pure functions
- Add component tests for UI logic
- Use `npm run test:coverage` to see coverage report

## Metrics and Monitoring

### Coverage Reports

Coverage reports are uploaded to Codecov after each CI run:

- Backend: `backend/coverage.xml`
- Frontend: `frontend/coverage/lcov.info`

### Local Coverage Viewing

**Backend:**

```bash
cd backend
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**Frontend:**

```bash
cd frontend
npm run test:coverage
open coverage/index.html
```

### VS Code Coverage Gutters

Install the "Coverage Gutters" extension to see coverage inline:

1. Run tests with coverage
2. Click "Watch" in status bar
3. Coverage highlights appear in editor

## Quality Gate Evolution

As the codebase matures, consider:

1. **Increasing thresholds:**

   - Pylint minimum score: 9.0 → 9.5
   - Test coverage: 80% → 85%
   - Complexity: CCN 15 → CCN 10

2. **Additional checks:**

   - Security scanning (Bandit for Python, npm audit)
   - Dependency vulnerability scanning
   - Performance benchmarks
   - Bundle size limits (Frontend)

3. **Automated fixes:**
   - Auto-format on commit (Black for Python, Prettier for TS)
   - Auto-organize imports
   - Auto-update dependencies

## References

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React Hooks Rules](https://react.dev/reference/rules)
- [Pylint Documentation](https://pylint.pycqa.org/)
- [ESLint Documentation](https://eslint.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
