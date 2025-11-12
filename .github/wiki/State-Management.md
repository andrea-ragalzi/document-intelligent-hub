# State Management Architecture

The application uses a modern, scalable state management architecture that separates **UI state** from **Server state**.

## Overview

### State Management Stack

- **Zustand** (1KB): Manages local UI state (modals, alerts, flags)
- **TanStack Query**: Manages server state (Firestore conversations)
- **React Hooks**: Component-level state and side effects

### Why This Architecture?

| Problem | Solution |
|---------|----------|
| Prop drilling through multiple components | Direct store access |
| State scattered across components | Centralized stores |
| Manual cache management | Automatic with TanStack Query |
| Complex async state handling | Built-in loading/error states |
| No optimistic updates | Built-in optimistic updates |
| Difficult debugging | Redux DevTools + React Query DevTools |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      React Components                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐              ┌────────────────────┐  │
│  │   Zustand Store  │              │  TanStack Query    │  │
│  │   (UI State)     │              │  (Server State)    │  │
│  ├──────────────────┤              ├────────────────────┤  │
│  │ • Modals         │              │ • Conversations    │  │
│  │ • Alerts         │              │ • Cache            │  │
│  │ • Flags          │              │ • Mutations        │  │
│  │ • Current ID     │              │ • Queries          │  │
│  └──────────────────┘              └────────────────────┘  │
│                                              │               │
│                                              ▼               │
│                                     ┌────────────────────┐  │
│                                     │    Firestore       │  │
│                                     │   (Persistence)    │  │
│                                     └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Zustand Store (UI State)

### Location
`frontend/stores/uiStore.ts`

### Responsibilities
- Modal state management (open/close)
- Alert messages (success/error/info)
- Current conversation tracking
- Saving flags and counters

### State Structure

```typescript
interface UIStore {
  // Alerts
  statusAlert: AlertState | null;
  uploadAlert: AlertState | null;
  
  // Modals
  renameModalOpen: boolean;
  confirmDeleteOpen: boolean;
  conversationToRename: { id: string; currentName: string } | null;
  conversationToDelete: { id: string; name: string } | null;
  
  // Conversation tracking
  currentConversationId: string | null;
  lastSavedMessageCount: number;
  isSaving: boolean;
  
  // Actions
  setStatusAlert: (alert: AlertState | null) => void;
  openRenameModal: (id: string, currentName: string) => void;
  closeRenameModal: () => void;
  openDeleteModal: (id: string, name: string) => void;
  closeDeleteModal: () => void;
  setCurrentConversation: (id: string | null) => void;
  updateSavedMessageCount: (count: number) => void;
  startSaving: () => void;
  finishSaving: () => void;
  resetConversation: () => void;
}
```

### Usage Example

```typescript
import { useUIStore } from "@/stores/uiStore";

function MyComponent() {
  // Subscribe only to what you need (prevents unnecessary re-renders)
  const { statusAlert, setStatusAlert } = useUIStore();
  
  const handleAction = () => {
    setStatusAlert({ 
      message: "Operation successful!", 
      type: "success" 
    });
  };
  
  return (
    <div>
      {statusAlert && <Alert {...statusAlert} />}
      <button onClick={handleAction}>Do Something</button>
    </div>
  );
}
```

### DevTools Integration

Zustand integrates with **Redux DevTools**:

1. Install [Redux DevTools Extension](https://github.com/reduxjs/redux-devtools)
2. Open DevTools in browser
3. Select "Redux" tab
4. View all actions and state changes in real-time

**Features:**
- ⏮️ Time-travel debugging
- 📊 Action history
- 🔍 State inspection
- 📸 State snapshots

## TanStack Query (Server State)

### Location
`frontend/hooks/queries/useConversationsQuery.ts`

### Responsibilities
- Fetching conversations from Firestore
- Creating new conversations
- Updating conversation names and history
- Deleting conversations
- Automatic caching and revalidation
- Optimistic updates

### Query Keys

```typescript
export const conversationKeys = {
  all: ["conversations"] as const,
  byUser: (userId: string) => ["conversations", userId] as const,
  detail: (id: string) => ["conversations", "detail", id] as const,
};
```

**Purpose:** Used for cache invalidation and refetching specific data.

### Hooks

#### 1. `useConversationsQuery`

Fetches all conversations for a user.

```typescript
const { 
  data: conversations,      // Conversation[]
  isLoading,                // boolean
  error,                    // Error | null
  refetch                   // () => Promise<void>
} = useConversationsQuery(userId);
```

**Features:**
- ✅ Automatic caching (30s stale time)
- ✅ Background refetch
- ✅ Error handling
- ✅ Loading states

#### 2. `useCreateConversation`

Creates a new conversation with optimistic updates.

```typescript
const createConversation = useCreateConversation(userId);

await createConversation.mutateAsync({
  name: "New Conversation",
  history: chatHistory
});
```

**Flow:**
1. 🔄 Optimistic update: Adds temporary conversation to UI
2. 📤 Sends request to Firestore
3. ✅ On success: Replaces temp with real data
4. ❌ On error: Rolls back to previous state

#### 3. `useUpdateConversationName`

Updates conversation name with optimistic updates.

```typescript
const updateName = useUpdateConversationName(userId);

await updateName.mutateAsync({
  id: "conv-123",
  newName: "Updated Name"
});
```

#### 4. `useUpdateConversationHistory`

Updates conversation messages (used for auto-save).

```typescript
const updateHistory = useUpdateConversationHistory(userId);

await updateHistory.mutateAsync({
  id: "conv-123",
  history: updatedMessages
});
```

**Optimization:** Does NOT trigger automatic refetch (too expensive for auto-save).

#### 5. `useDeleteConversation`

Deletes a conversation with optimistic updates.

```typescript
const deleteConversation = useDeleteConversation(userId);

await deleteConversation.mutateAsync("conv-123");
```

### Optimistic Updates

All mutations implement optimistic updates for instant UI feedback:

```typescript
onMutate: async (newData) => {
  // 1. Cancel ongoing queries
  await queryClient.cancelQueries({ queryKey });
  
  // 2. Snapshot current data
  const previousData = queryClient.getQueryData(queryKey);
  
  // 3. Optimistically update UI
  queryClient.setQueryData(queryKey, (old) => {
    // Update logic
  });
  
  // 4. Return context for rollback
  return { previousData };
},

onError: (err, variables, context) => {
  // Rollback on error
  queryClient.setQueryData(queryKey, context.previousData);
},

onSuccess: () => {
  // Invalidate cache to refetch fresh data
  queryClient.invalidateQueries({ queryKey });
}
```

### Query Configuration

Located in `providers/QueryProvider.tsx`:

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,        // 30 seconds
      gcTime: 5 * 60 * 1000,       // 5 minutes (garbage collection)
      retry: 1,                     // Retry once on failure
      refetchOnWindowFocus: false,  // Don't refetch on window focus
    },
    mutations: {
      retry: 1,
    },
  },
});
```

**Configuration Guide:**

| Option | Value | Reason |
|--------|-------|--------|
| `staleTime` | 30s | Data stays "fresh" for 30 seconds |
| `gcTime` | 5min | Cache cleaned after 5 minutes of inactivity |
| `retry` | 1 | Retry once on network failure |
| `refetchOnWindowFocus` | false | Prevents excessive refetching |

### DevTools Integration

TanStack Query includes built-in DevTools:

```typescript
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

<QueryClientProvider client={queryClient}>
  {children}
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

**Features:**
- 📊 Query status visualization
- ⚡ Active/inactive queries
- 🔄 Mutation tracking
- 📈 Network request timeline
- 🔍 Cache inspection

## Integration in Components

### Before (useState)

```typescript
function Page() {
  const [statusAlert, setStatusAlert] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchConversations = async () => {
      setLoading(true);
      const data = await loadFromFirestore();
      setConversations(data);
      setLoading(false);
    };
    fetchConversations();
  }, []);
  
  const handleDelete = async (id) => {
    await deleteFromFirestore(id);
    // Manual refetch needed
    const data = await loadFromFirestore();
    setConversations(data);
  };
}
```

**Problems:**
- ❌ 10+ useState declarations
- ❌ Manual loading states
- ❌ Manual error handling
- ❌ Manual cache management
- ❌ No optimistic updates
- ❌ Prop drilling nightmare

### After (Zustand + TanStack Query)

```typescript
function Page() {
  // UI State (1 line)
  const { statusAlert, setStatusAlert, modalOpen, openModal } = useUIStore();
  
  // Server State (1 line)
  const { data: conversations = [], isLoading } = useConversationsQuery(userId);
  const deleteConversation = useDeleteConversation(userId);
  
  const handleDelete = async (id) => {
    // Automatic optimistic update + refetch
    await deleteConversation.mutateAsync(id);
  };
}
```

**Benefits:**
- ✅ 2 lines instead of 10+
- ✅ Automatic loading states
- ✅ Automatic error handling
- ✅ Automatic cache management
- ✅ Built-in optimistic updates
- ✅ No prop drilling

## Auto-Save Implementation

The auto-save feature demonstrates the power of this architecture:

```typescript
useEffect(() => {
  // Only save when assistant finishes responding
  if (isLoading || !userId || chatHistory.length < 2) return;
  
  const autoSave = async () => {
    startSaving(); // UI store flag
    
    if (currentConversationId) {
      // Update existing conversation
      await updateHistory.mutateAsync({
        id: currentConversationId,
        history: chatHistory
      });
      updateSavedMessageCount(chatHistory.length);
    } else {
      // Create new conversation
      await createConversation.mutateAsync({
        name: generateName(),
        history: chatHistory
      });
      // ID will be set by separate useEffect
    }
    
    finishSaving();
  };
  
  // Debounce for 500ms
  const timeoutId = setTimeout(autoSave, 500);
  return () => clearTimeout(timeoutId);
}, [chatHistory, isLoading, currentConversationId]);
```

**Features:**
1. ⏰ Debounced (500ms)
2. 🎯 Saves only when assistant finishes
3. 🆕 Creates new conversation on first save
4. 📝 Updates existing conversation on subsequent saves
5. 🚀 Optimistic updates for instant feedback
6. 🔄 Automatic rollback on error

## Best Practices

### 1. Separate UI State from Server State

```typescript
// ❌ BAD: Mixing concerns
const [conversations, setConversations] = useState([]); // Server state
const [modalOpen, setModalOpen] = useState(false);      // UI state

// ✅ GOOD: Clear separation
const { data: conversations } = useConversationsQuery(userId); // Server state
const { modalOpen } = useUIStore();                             // UI state
```

### 2. Use Granular Selectors

```typescript
// ❌ BAD: Re-renders on ANY store change
const store = useUIStore();

// ✅ GOOD: Re-renders only when statusAlert changes
const statusAlert = useUIStore(state => state.statusAlert);
```

### 3. Leverage Optimistic Updates

```typescript
// ❌ BAD: Wait for server response
const handleDelete = async (id) => {
  await deleteFromServer(id);
  refetch(); // Wait for confirmation
};

// ✅ GOOD: Instant UI feedback
const deleteConversation = useDeleteConversation(userId);
await deleteConversation.mutateAsync(id); // Optimistic update
```

### 4. Use Query Keys Consistently

```typescript
// ✅ Centralized query keys
export const conversationKeys = {
  all: ["conversations"],
  byUser: (userId) => ["conversations", userId],
};

// Easy invalidation
queryClient.invalidateQueries({ 
  queryKey: conversationKeys.byUser(userId) 
});
```

## Testing

### Testing Zustand Stores

```typescript
import { renderHook, act } from '@testing-library/react';
import { useUIStore } from '@/stores/uiStore';

describe('UIStore', () => {
  it('should open and close modal', () => {
    const { result } = renderHook(() => useUIStore());
    
    act(() => {
      result.current.openRenameModal('conv-1', 'Old Name');
    });
    
    expect(result.current.renameModalOpen).toBe(true);
    expect(result.current.conversationToRename).toEqual({
      id: 'conv-1',
      currentName: 'Old Name'
    });
  });
});
```

### Testing TanStack Query Hooks

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { useConversationsQuery } from '@/hooks/queries/useConversationsQuery';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useConversationsQuery', () => {
  it('should fetch conversations', async () => {
    const { result } = renderHook(
      () => useConversationsQuery('user-123'),
      { wrapper: createWrapper() }
    );
    
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(3);
  });
});
```

## Performance Optimization

### Selector Optimization

```typescript
// ❌ Creates new object on every render
const { statusAlert, uploadAlert } = useUIStore();

// ✅ Memoized selector
const statusAlert = useUIStore(state => state.statusAlert);
const uploadAlert = useUIStore(state => state.uploadAlert);
```

### Query Prefetching

```typescript
// Prefetch data on hover for instant navigation
const queryClient = useQueryClient();

const prefetchConversation = (id: string) => {
  queryClient.prefetchQuery({
    queryKey: conversationKeys.detail(id),
    queryFn: () => fetchConversation(id),
  });
};

<button onMouseEnter={() => prefetchConversation('conv-1')}>
  Open Conversation
</button>
```

## Migration Guide

See the complete migration guide from useState to Zustand + TanStack Query in the [Development Workflow](Development-Workflow) wiki page.

## Further Reading

- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [State Management Patterns](https://kentcdodds.com/blog/application-state-management-with-react)
- [Optimistic Updates Guide](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)

## Next Steps

- [Hooks Reference](Hooks-Reference) - All custom hooks
- [Store Reference](Store-Reference) - Store API documentation
- [Frontend Components](Frontend-Components) - Component architecture
