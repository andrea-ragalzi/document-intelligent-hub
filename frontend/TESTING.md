# Frontend Testing Guide

## Overview

This frontend uses **Vitest** with **React Testing Library** for comprehensive testing of hooks, components, and integration flows.

## Test Structure

```
frontend/test/
├── setup.ts                        # Global test configuration
├── hooks/
│   ├── useTheme.test.ts           # Theme management tests
│   ├── useUserId.test.ts          # User ID generation tests
│   └── useConversations.test.ts   # Conversation CRUD tests
└── components/
    └── AlertMessage.test.tsx      # Alert component tests
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- useTheme.test.ts
```

## VSCode Integration

The **Vitest extension** (`vitest.explorer`) is configured in `.vscode/settings.json`:

- **Test Explorer**: View all tests in the sidebar
- **Run/Debug**: Click on test cases to run individually
- **CodeLens**: Run tests directly from editor
- **Auto-discovery**: Tests are automatically detected

### Test Explorer Shortcuts

- `Ctrl+; A` - Run all tests
- `Ctrl+; F` - Run failed tests
- `Ctrl+; L` - Run last test
- Click ▶️ icon next to test to run individually

## Coverage Thresholds

Configured in `vitest.config.ts`:

- **Lines**: 80%
- **Functions**: 80%
- **Branches**: 75%
- **Statements**: 80%

## Test Structure Example

```typescript
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should toggle theme from light to dark', () => {
    const { result } = renderHook(() => useTheme())
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('dark')
  })
})
```

## Current Test Coverage

✅ **28 tests passing**

- **Hooks**: 21 tests (useTheme, useUserId, useConversations)
- **Components**: 7 tests (AlertMessage)

### Test Categories

1. **Hook Tests**
   - Theme persistence and toggling
   - User ID generation and localStorage
   - Conversation CRUD operations
   - Multi-tenant isolation

2. **Component Tests**
   - Conditional rendering
   - Style variants (success/error/info)
   - Dark mode support
   - Accessibility

## Best Practices

1. **Cleanup**: Use `beforeEach` to clear localStorage/state
2. **Async Testing**: Use `waitFor` for async state updates
3. **User Events**: Use `@testing-library/user-event` for interactions
4. **Accessibility**: Test ARIA attributes and keyboard navigation
5. **Isolation**: Each test should be independent

## Next Steps

- [ ] Add tests for `useChatAI` hook (streaming, error handling)
- [ ] Add tests for `ChatSection` component
- [ ] Add E2E integration tests (upload → chat → save flow)
- [ ] Add visual regression tests with Playwright
