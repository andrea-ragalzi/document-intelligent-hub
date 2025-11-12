# Frontend Architecture

The frontend is a modern Next.js 16 application with TypeScript, providing a responsive and intuitive interface for the RAG document chat system.

## 📁 Directory Structure

```
frontend/
├── app/
│   ├── api/
│   │   └── chat/
│   │       └── route.ts       # API proxy route for streaming
│   ├── login/
│   │   └── page.tsx           # Login page
│   ├── signup/
│   │   └── page.tsx           # Signup page
│   ├── layout.tsx             # Root layout with providers
│   ├── page.tsx               # Main application page
│   └── globals.css            # Global styles
├── components/
│   ├── AlertMessage.tsx       # Notification messages
│   ├── ChatMessageDisplay.tsx # Individual message display
│   ├── ChatSection.tsx        # Main chat interface
│   ├── ConfirmModal.tsx       # Confirmation dialogs
│   ├── ConversationList.tsx   # Saved conversations list
│   ├── LoginForm.tsx          # Login form component
│   ├── ProtectedRoute.tsx     # Authentication guard
│   ├── RenameModal.tsx        # Rename conversation modal
│   ├── SaveModal.tsx          # Save conversation modal
│   ├── Sidebar.tsx            # Left sidebar container
│   ├── SignupForm.tsx         # Signup form component
│   ├── UploadSection.tsx      # Document upload section
│   └── UserProfile.tsx        # User profile dropdown
├── contexts/
│   └── AuthContext.tsx        # Firebase authentication context
├── hooks/
│   ├── queries/
│   │   └── useConversationsQuery.ts  # TanStack Query hooks
│   ├── useChatAI.ts           # Vercel AI SDK chat hook
│   ├── useConversations.ts    # Legacy localStorage hook
│   ├── useDocumentUpload.ts   # Document upload logic
│   ├── useRAGChat.ts          # Legacy RAG chat hook
│   ├── useTheme.ts            # Dark/light theme toggle
│   └── useUserId.ts           # Firebase user ID hook
├── lib/
│   ├── constants.ts           # Application constants
│   ├── conversationsService.ts # Firestore CRUD operations
│   ├── firebase.ts            # Firebase configuration
│   └── types.ts               # TypeScript type definitions
├── providers/
│   └── QueryProvider.tsx      # TanStack Query provider
├── stores/
│   └── uiStore.ts             # Zustand UI state store
├── public/                    # Static assets
├── test/                      # Frontend tests
│   ├── setup.ts
│   ├── components/
│   └── hooks/
├── .env.local                 # Environment variables (not tracked)
├── next.config.ts             # Next.js configuration
├── package.json               # Dependencies
├── tailwind.config.js         # Tailwind CSS config
├── tsconfig.json              # TypeScript config
└── vitest.config.ts           # Vitest test config
```

## 🏗️ Architecture Layers

### 1. **App Router** (`app/`)

Next.js 16 App Router with server and client components.

#### **Main Page** (`page.tsx`)

The primary application orchestrator that brings together all features.

**Key Responsibilities**:
- Coordinate all custom hooks
- Manage application-wide state
- Handle user interactions
- Orchestrate data flow between components

**State Management**:
- Zustand for UI state (modals, alerts, conversation tracking)
- TanStack Query for server state (Firestore conversations)
- Vercel AI SDK for chat streaming

**Hooks Used**:
```typescript
const { theme, toggleTheme } = useTheme();
const { userId, isAuthReady } = useUserId();
const { file, handleFileChange, handleUpload, isUploading, uploadAlert } = useDocumentUpload();
const { chatHistory, input, handleInputChange, handleSubmit, isLoading, setMessages } = useChatAI({ userId });
const { statusAlert, renameModalOpen, confirmDeleteOpen, ... } = useUIStore();
const { data: savedConversations } = useConversationsQuery(userId);
```

#### **API Route** (`api/chat/route.ts`)

Edge function that proxies chat requests to the FastAPI backend.

**Features**:
- Server-side API proxy
- Streaming response handling
- Vercel AI SDK compatible format
- Error handling

**Flow**:
```
Frontend useChatAI() 
  → POST /api/chat 
  → FastAPI /rag/query/ 
  → Stream response back
  → Vercel AI SDK processes stream
```

### 2. **Components** (`components/`)

Reusable React components organized by functionality.

#### **Layout Components**

**Sidebar.tsx**
- Container for upload section and conversations list
- Displays user ID
- Responsive collapsible design

**ChatSection.tsx**
- Main chat interface
- Message display with auto-scroll
- Input field and submit button
- New conversation button

#### **Feature Components**

**UploadSection.tsx**
- Drag-and-drop file upload
- File type validation (PDF only)
- Upload progress indicator
- Success/error alerts

**ConversationList.tsx**
- Display saved conversations
- Load, rename, delete actions
- Timestamp display
- Empty state message

**ChatMessageDisplay.tsx**
- Render individual chat messages
- User vs assistant styling
- Source documents display
- Loading state for streaming

#### **Modal Components**

**SaveModal.tsx**
- Name input for saving conversations
- Form validation
- Error display

**RenameModal.tsx**
- Edit conversation name
- Current name display
- Validation

**ConfirmModal.tsx**
- Generic confirmation dialog
- Variant support (danger, warning, info)
- Customizable buttons

#### **Auth Components**

**ProtectedRoute.tsx**
- Authentication guard wrapper
- Redirect to login if not authenticated
- Loading state

**LoginForm.tsx / SignupForm.tsx**
- Firebase authentication forms
- Email/password validation
- Error handling

**UserProfile.tsx**
- User info dropdown
- Sign out button
- Profile display

### 3. **State Management**

#### **Zustand Store** (`stores/uiStore.ts`)

Lightweight client-side state management.

**State**:
```typescript
interface UIStore {
  // Alerts
  statusAlert: AlertState | null;
  
  // Modals
  renameModalOpen: boolean;
  confirmDeleteOpen: boolean;
  
  // Conversation tracking
  conversationToRename: { id: string; currentName: string } | null;
  conversationToDelete: { id: string; name: string } | null;
  currentConversationId: string | null;
  lastSavedMessageCount: number;
  isSaving: boolean;
  
  // Actions (15+ methods)
  setStatusAlert: (alert: AlertState | null) => void;
  openRenameModal: (id: string, name: string) => void;
  closeRenameModal: () => void;
  // ... more actions
}
```

**Features**:
- Redux DevTools integration
- Time-travel debugging
- Persist to localStorage (optional)
- Type-safe with TypeScript

#### **TanStack Query** (`providers/QueryProvider.tsx`)

Server state management with automatic caching and refetching.

**Configuration**:
```typescript
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,      // 30 seconds
      gcTime: 5 * 60 * 1000,     // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})
```

**Query Hooks** (`hooks/queries/useConversationsQuery.ts`):
- `useConversationsQuery()` - Fetch conversations
- `useCreateConversation()` - Create new conversation
- `useUpdateConversationName()` - Rename conversation
- `useUpdateConversationHistory()` - Auto-save messages
- `useDeleteConversation()` - Delete conversation

**Features**:
- Automatic background refetching
- Optimistic updates
- Automatic rollback on error
- Cache invalidation
- React Query DevTools

### 4. **Custom Hooks** (`hooks/`)

Reusable logic encapsulated in hooks.

#### **useChatAI.ts**

Integrates Vercel AI SDK for streaming chat.

**Features**:
- Real-time streaming responses
- Message history management
- Automatic message formatting
- Error handling

**API**:
```typescript
const {
  chatHistory,      // Message[] - All messages
  input,            // string - Current input
  handleInputChange, // Update input
  handleSubmit,     // Send message
  isLoading,        // Streaming in progress
  setMessages,      // Load conversation
} = useChatAI({ userId });
```

#### **useDocumentUpload.ts**

Handles PDF upload to backend.

**Features**:
- File validation
- FormData construction
- Upload progress
- Alert management

**API**:
```typescript
const {
  file,             // File | null
  isUploading,      // boolean
  uploadAlert,      // AlertState
  handleFileChange, // (e: ChangeEvent<HTMLInputElement>) => void
  handleUpload,     // (e: FormEvent, userId: string) => Promise<void>
} = useDocumentUpload();
```

#### **useTheme.ts**

Dark/light mode toggle with persistence.

**Features**:
- System preference detection
- localStorage persistence
- CSS class toggle on `<html>`

**API**:
```typescript
const { theme, toggleTheme } = useTheme();
// theme: 'light' | 'dark'
```

#### **useUserId.ts**

Firebase authenticated user ID.

**Features**:
- Firebase auth state listener
- User ID extraction
- Auth ready state

**API**:
```typescript
const { userId, isAuthReady } = useUserId();
```

### 5. **Services** (`lib/`)

#### **conversationsService.ts**

Firestore CRUD operations for conversations.

**Functions**:
- `saveConversationToFirestore()` - Create conversation
- `loadConversationsFromFirestore()` - Fetch all conversations
- `updateConversationNameInFirestore()` - Rename
- `updateConversationHistoryInFirestore()` - Update messages
- `deleteConversationFromFirestore()` - Delete
- `migrateLocalStorageToFirestore()` - Migration utility

**Multi-Tenant**:
- All operations filtered by `userId`
- Automatic user-specific queries
- Timestamp management

#### **firebase.ts**

Firebase configuration and initialization.

**Exports**:
```typescript
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
```

### 6. **Context Providers** (`contexts/`)

#### **AuthContext.tsx**

Firebase authentication context.

**Features**:
- Current user state
- Auth loading state
- Signin/signup methods
- Signout method
- Auth state persistence

**Usage**:
```typescript
const { user, loading, signin, signup, signout } = useAuth();
```

## 🔄 Data Flow

### Conversation Save Flow

```
1. User sends message
   ↓
2. Vercel AI SDK streams response
   ↓
3. isLoading changes from true → false
   ↓
4. useEffect triggers auto-save
   ↓
5. Check if conversation exists (currentConversationId)
   ↓
6a. Exists → updateConversationHistory.mutateAsync()
6b. New → createConversation.mutateAsync()
   ↓
7. TanStack Query:
   - Optimistic update (UI updates immediately)
   - API call to Firestore
   - On success: invalidate query, refetch
   - On error: rollback to previous state
   ↓
8. UI shows updated conversation list
```

### Document Upload Flow

```
1. User selects PDF file
   ↓
2. handleFileChange validates file type
   ↓
3. User clicks upload button
   ↓
4. handleUpload creates FormData
   ↓
5. POST to /rag/upload/
   ↓
6. Backend processes and indexes
   ↓
7. Success response
   ↓
8. Alert displayed
   ↓
9. File input reset
```

## 🎨 Styling

**Framework**: Tailwind CSS 3.x

**Features**:
- Utility-first CSS
- Dark mode support via `dark:` prefix
- Responsive design with breakpoints
- Custom color palette
- Animation classes

**Dark Mode Implementation**:
```typescript
// useTheme hook adds 'dark' class to <html>
document.documentElement.classList.add('dark');

// Components use dark: variant
<div className="bg-white dark:bg-gray-800">
```

## 🧪 Testing

**Framework**: Vitest + React Testing Library

**Test Structure**:
```
test/
├── setup.ts              # Test environment setup
├── components/           # Component tests
│   ├── ChatSection.test.tsx
│   └── Sidebar.test.tsx
└── hooks/                # Hook tests
    ├── useTheme.test.ts
    └── useDocumentUpload.test.ts
```

**Run Tests**:
```bash
# Run all tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# UI mode
npm run test:ui
```

## 📦 Key Dependencies

**Core**:
- `next@16.0` - React framework
- `react@19.0` - UI library
- `typescript@5.x` - Type safety
- `tailwindcss@3.x` - Styling

**State Management**:
- `zustand@5.0` - Client state
- `@tanstack/react-query@5.x` - Server state

**AI & Chat**:
- `ai@3.x` - Vercel AI SDK
- `openai@4.x` - OpenAI integration

**Firebase**:
- `firebase@11.x` - Auth & Firestore

**UI**:
- `lucide-react@0.x` - Icons
- `react-markdown@9.x` - Markdown rendering

**Testing**:
- `vitest@2.x` - Test runner
- `@testing-library/react@16.x` - Component testing

## 🚀 Performance Optimizations

**Current**:
- TanStack Query caching (30s stale time)
- Automatic request deduplication
- Optimistic UI updates
- Lazy loading with Next.js dynamic imports
- Image optimization (next/image)

**Future**:
- [ ] Virtual scrolling for long conversations
- [ ] Service Worker for offline support
- [ ] Request batching
- [ ] Component code splitting

## 🔐 Security

**Implemented**:
- Firebase Authentication
- Protected routes
- Environment variables for secrets
- CORS configuration
- Input validation
- XSS prevention (React escaping)

**Future**:
- [ ] Rate limiting
- [ ] CSRF protection
- [ ] Content Security Policy
- [ ] Secure headers

## 📱 Responsive Design

**Breakpoints** (Tailwind default):
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

**Mobile-First**:
- Base styles for mobile
- Progressive enhancement for larger screens
- Touch-friendly UI elements
- Responsive layouts with flexbox/grid

## 🎯 Key Features

✅ Real-time chat streaming  
✅ Dark mode support  
✅ Conversation persistence (Firestore)  
✅ Auto-save conversations  
✅ Multi-tenant support  
✅ Responsive design  
✅ Type-safe with TypeScript  
✅ Modern state management  
✅ Authentication & authorization  
✅ Optimistic UI updates  
✅ Error handling & recovery  

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [Vercel AI SDK Documentation](https://sdk.vercel.ai/docs)
- [Firebase Documentation](https://firebase.google.com/docs)
