# Pre-Commit Configuration Guide

## Overview

This project uses `pre-commit` hooks to enforce code quality and security standards before commits.

## Installation

```bash
# Install pre-commit (first time only)
pip install pre-commit

# Install git hooks
pre-commit install
```

## What Gets Checked

### 🔒 Security (CRITICAL - Will Block Commits)

- ✅ **AWS Credentials Detection** - Blocks AWS access keys
- ✅ **Private Key Detection** - Blocks RSA/DSA/EC private keys
- ✅ **Gitleaks** - Advanced secret scanning (API keys, tokens, passwords)

### 🧹 Code Quality

- ✅ **YAML/JSON Validation** - Syntax checking
- ✅ **End of File Fixer** - Ensures newline at end of files
- ✅ **Trailing Whitespace** - Removes unnecessary whitespace
- ✅ **Executable Shebangs** - Validates script headers
- ✅ **Large Files** - Blocks files > 500KB
- ✅ **Merge Conflicts** - Detects unresolved conflicts
- ✅ **Case Conflicts** - Prevents filesystem case issues
- ✅ **Line Endings** - Normalizes to LF (Unix)

### 🐍 Python (Backend)

- ✅ **Black** - Code formatting (auto-fix)

### 🎨 TypeScript/JavaScript (Frontend)

- ✅ **Prettier** - Code formatting (auto-fix)

## Usage

### Automatic (On Commit)

Pre-commit hooks run automatically when you `git commit`:

```bash
git add .
git commit -m "Your commit message"
# ← Hooks run here automatically
```

If a check fails, the commit is blocked and you must fix the issues.

### Manual Run

Test hooks without committing:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run gitleaks --all-files

# Run on staged files only
pre-commit run
```

### Update Hooks

Update to latest hook versions:

```bash
pre-commit autoupdate
```

## Configuration Files

### `.pre-commit-config.yaml`

Main configuration file defining which hooks to run and their settings.

### `.gitleaks.toml`

Gitleaks-specific configuration:

- **Allowlist** - Patterns to ignore (e.g., example keys)
- **Paths** - Directories to skip (e.g., `node_modules/`, `.venv/`)
- **Rules** - Custom exceptions for specific files

## Bypassing Hooks (Emergency Only)

```bash
# Skip ALL hooks (use with extreme caution!)
git commit --no-verify -m "Emergency fix"

# Skip specific secret in commit message
git commit -m "Add config file gitleaks:allow"
```

⚠️ **Warning:** Only bypass hooks if you understand the security implications!

## Troubleshooting

### Hook Fails on File Outside Project

If a hook fails on files in `.venv/` or `node_modules/`, they should already be excluded. Check `.pre-commit-config.yaml` exclude patterns.

### Gitleaks False Positive

Add pattern to `.gitleaks.toml` allowlist:

```toml
[allowlist]
regexes = [
  '''your-safe-pattern-here''',
]
```

### Black/Prettier Formatting Conflicts

1. Run formatters manually first:

   ```bash
   # Backend
   cd backend && black app/

   # Frontend
   cd frontend && npx prettier --write .
   ```

2. Then commit

### Performance Issues

If hooks are slow:

```bash
# Skip on large commits temporarily
git commit --no-verify

# Or reduce scope
pre-commit run --files backend/app/specific_file.py
```

## CI/CD Integration

Pre-commit hooks also run in GitHub Actions on every push/PR:

```yaml
# .github/workflows/quality-gate.yml
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

## Files Excluded from Checks

### Always Excluded

- `node_modules/`, `.venv/`, `venv/`
- `.next/`, `__pycache__/`, `.pytest_cache/`
- `chroma_db/`, `logs/`
- `*.lock` files, minified files (`.min.js`, `.min.css`)

### Security Exceptions

- `.env.example`, `.env.local.example` - Template files
- `backend/app/config/firebase-service-account.json` - Gitignored, not scanned
- Test fixtures in `tests/` directories

## Best Practices

1. **Install hooks immediately** after cloning the repo
2. **Run `pre-commit run --all-files`** before pushing
3. **Never commit real secrets** - use environment variables
4. **Keep hooks updated** - run `pre-commit autoupdate` monthly
5. **Fix issues before committing** - don't bypass hooks casually

## Support

For issues with pre-commit configuration:

1. Check [pre-commit docs](https://pre-commit.com/)
2. Review `.pre-commit-config.yaml` comments
3. Open issue in project repo

---

**Remember:** These hooks protect the codebase and your credentials. Work with them, not against them! 🛡️
