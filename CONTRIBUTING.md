# 🤝 Contributing to Document Intelligent Hub

Thank you for your interest in contributing! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)

## 🌟 Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming community.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- Git
- OpenAI API Key

### Initial Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then:
   git clone https://github.com/YOUR-USERNAME/document-intelligent-hub.git
   cd document-intelligent-hub
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/andrea-ragalzi/document-intelligent-hub.git
   ```

3. **Install dependencies**
   ```bash
   # Backend
   cd backend
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   
   # Frontend
   cd ../frontend
   npm install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## 🔄 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes

### 2. Make Changes

Follow the [Coding Standards](#coding-standards) below.

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest

# Frontend build test
cd frontend
npm run build
```

### 4. Commit

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add document deletion endpoint"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots (if UI changes)
- Test results

## 📝 Coding Standards

### Python (Backend)

**Style Guide**: Follow PEP 8

```python
# Good
def process_document(file_path: str, user_id: str) -> dict:
    """Process a document and return metadata.
    
    Args:
        file_path: Path to the document file
        user_id: Unique user identifier
        
    Returns:
        Dictionary containing document metadata
    """
    # Implementation
    pass

# Use type hints
# Add docstrings
# Keep functions focused and small
```

**Formatting**:
```bash
# Install black
pip install black

# Format code
black app/ tests/
```

**Imports**:
```python
# Standard library
import os
from typing import List, Dict

# Third-party
from fastapi import APIRouter
from pydantic import BaseModel

# Local
from app.services.rag_service import rag_service
```

### TypeScript (Frontend)

**Style Guide**: Use ESLint configuration

```typescript
// Good
interface UserProfile {
  id: string;
  name: string;
  email: string;
}

const fetchUserProfile = async (userId: string): Promise<UserProfile> => {
  // Implementation
};

// Use TypeScript types
// Prefer functional components
// Use React hooks properly
```

**Formatting**:
```bash
# Lint
npm run lint

# Auto-fix
npm run lint -- --fix
```

### General Principles

1. **DRY (Don't Repeat Yourself)**: Reuse code through functions/components
2. **KISS (Keep It Simple)**: Prefer simple, readable solutions
3. **SOLID**: Follow SOLID principles for OOP
4. **Comments**: Write self-documenting code; add comments for complex logic
5. **Error Handling**: Always handle errors gracefully
6. **Security**: Never commit secrets or API keys

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_endpoints.py

# Run with coverage
pytest --cov=app --cov-report=html

# Watch mode (with pytest-watch)
ptw
```

**Test Structure**:
```python
# tests/test_feature.py
def test_feature_success(client, test_user_id):
    """Test successful feature execution."""
    response = client.post("/endpoint", json={"data": "value"})
    assert response.status_code == 200
    assert "expected_key" in response.json()

def test_feature_validation_error(client):
    """Test validation error handling."""
    response = client.post("/endpoint", json={})
    assert response.status_code == 422
```

### Frontend Tests

```bash
cd frontend

# Build test
npm run build

# Lint
npm run lint
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
./test.sh
```

## 📤 Submitting Changes

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No merge conflicts with main

### Pull Request Process

1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill in the template

4. **Respond to reviews**
   - Address feedback promptly
   - Push additional commits if needed
   - Mark conversations as resolved

5. **Merge**
   - Once approved, a maintainer will merge your PR
   - Delete your branch after merge

## 📁 Project Structure

```
document-intelligent-hub/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database clients
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic models
│   │   └── services/       # Business logic
│   ├── tests/              # Test suite
│   ├── main.py             # App entry point
│   └── pyproject.toml      # Dependencies
├── frontend/               # Next.js frontend
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── hooks/              # Custom hooks
│   ├── lib/                # Utilities
│   └── package.json        # Dependencies
├── .github/                # GitHub workflows
├── docker-compose.yml      # Docker orchestration
└── README.md               # Documentation
```

## 🐛 Reporting Bugs

### Before Reporting

- Search existing issues
- Check documentation
- Try latest version

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Screenshots**
If applicable

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.12]
- Node: [e.g., 22.0]
- Docker: [e.g., 24.0]

**Additional Context**
Any other relevant information
```

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if it's already requested
2. Explain the use case
3. Describe the proposed solution
4. Consider alternatives

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## ❓ Questions

- Open a GitHub Discussion
- Check existing issues
- Review documentation

---

Thank you for contributing! 🙏
