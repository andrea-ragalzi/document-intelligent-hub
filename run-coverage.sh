#!/bin/bash

# Script per eseguire tutti i test con coverage e visualizzare in VSCode

set -e

echo "🧪 Running Backend Tests with Coverage..."
cd backend
.venv/bin/python -m pytest --cov=app --cov-report=lcov --cov-report=term -v tests/
cd ..

echo ""
echo "🧪 Running Frontend Tests with Coverage..."
cd frontend
npm run test:coverage
cd ..

echo ""
echo "✅ Coverage files generated:"
echo "   - backend/coverage.lcov"
echo "   - frontend/coverage/lcov.info"
echo ""
echo "💡 To view coverage in VSCode:"
echo "   1. Open a source file (e.g., app/routers/rag_router.py or hooks/useTheme.ts)"
echo "   2. Press Ctrl+Shift+7 (or Cmd+Shift+7 on Mac)"
echo "   3. Green lines = covered, Red lines = not covered"
echo ""
echo "🌐 Or use Vitest UI for frontend:"
echo "   cd frontend && npm run test:ui"

