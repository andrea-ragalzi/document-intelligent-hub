# Common Issues & Solutions

Solutions to frequently encountered problems.

## Installation Issues

### Backend Won't Start

**Problem**: `poetry run uvicorn main:app --reload` fails

**Solutions**:

1. **Module Not Found**
   ```bash
   poetry install
   poetry update
   ```

2. **Port Already in Use**
   ```bash
   # Use different port
   uvicorn main:app --port 8001
   
   # Or kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   ```

3. **ChromaDB Error**
   ```bash
   # Delete and recreate database
   rm -rf backend/chroma_db
   # Restart backend
   ```

### Frontend Won't Start

**Problem**: `npm run dev` fails

**Solutions**:

1. **Module Not Found**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Port 3000 In Use**
   ```bash
   PORT=3001 npm run dev
   ```

3. **Build Errors**
   ```bash
   rm -rf .next
   npm run dev
   ```

## Firebase Issues

### Authentication Not Working

**Problem**: Can't log in or sign up

**Solutions**:

1. **Check Firebase Config**
   ```bash
   # Verify .env.local has correct values
   cat frontend/.env.local | grep FIREBASE
   ```

2. **Enable Email/Password Auth**
   - Go to Firebase Console
   - Authentication → Sign-in method
   - Enable Email/Password

3. **Check Console Errors**
   ```javascript
   // Browser console
   // Look for Firebase init errors
   ```

### Firestore Permission Denied

**Problem**: Can't read/write conversations

**Solutions**:

1. **Publish Security Rules**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /conversations/{conversationId} {
         allow read, write: if request.auth != null && 
                             request.auth.uid == resource.data.userId;
         allow create: if request.auth != null;
       }
     }
   }
   ```
   - Save and **Publish** rules

2. **Check User is Authenticated**
   ```typescript
   // Console log
   console.log('User ID:', userId);
   // Should not be null
   ```

3. **Verify Database Mode**
   - Firestore should be in "production mode"
   - Not "locked mode"

## Document Upload Issues

### Upload Fails

**Problem**: Document won't upload

**Solutions**:

1. **Check File Type**
   - Only PDF supported currently
   - Max size: 50MB

2. **Backend Not Running**
   ```bash
   # Check backend health
   curl http://localhost:8000/health
   ```

3. **CORS Error**
   ```python
   # backend/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Document Processing Hangs

**Problem**: Upload never completes

**Solutions**:

1. **Check Backend Logs**
   ```bash
   # Look for errors in terminal
   ```

2. **File Too Large**
   - Try smaller file
   - Check backend memory limits

3. **ChromaDB Issue**
   ```bash
   # Reset database
   rm -rf backend/chroma_db
   ```

## Chat Issues

### No Response from Chat

**Problem**: Message sent but no response

**Solutions**:

1. **Backend Not Running**
   ```bash
   curl http://localhost:8000/health
   ```

2. **No Document Uploaded**
   - Upload a document first
   - System needs context to answer

3. **API Key Missing**
   ```bash
   # Check .env
   cat backend/.env | grep LLM_API_KEY
   ```

4. **Check Browser Console**
   ```javascript
   // Look for fetch errors
   // Check Network tab
   ```

### Streaming Not Working

**Problem**: Response appears all at once

**Solutions**:

1. **Check Vercel AI SDK Setup**
   ```typescript
   // Should use useChat hook
   import { useChat } from 'ai/react';
   ```

2. **Backend Streaming Config**
   ```python
   # Should return StreamingResponse
   return StreamingResponse(
       stream_response(messages),
       media_type="text/event-stream"
   )
   ```

### Response is Wrong/Irrelevant

**Problem**: AI gives incorrect answers

**Solutions**:

1. **Document Not Processed**
   - Re-upload document
   - Check backend logs for processing errors

2. **Improve Query**
   - Be more specific
   - Reference document sections
   - Example: "According to page 5, what..."

3. **Adjust RAG Parameters**
   ```python
   # backend/.env
   TOP_K_RESULTS=10  # Retrieve more chunks
   SIMILARITY_THRESHOLD=0.6  # Lower threshold
   ```

## Conversation Management Issues

### Conversations Not Saving

**Problem**: Auto-save not working

**Solutions**:

1. **Check Authentication**
   ```typescript
   // User must be logged in
   console.log('User ID:', userId);
   ```

2. **Check Firestore Connection**
   ```typescript
   // Browser console
   // Look for Firestore errors
   ```

3. **Wait for Auto-save**
   - Auto-save triggers 500ms after AI finishes
   - Check console logs for save confirmation

### Can't Load Conversations

**Problem**: Saved conversations don't appear

**Solutions**:

1. **Wrong Account**
   - Ensure logged in with same account
   - Conversations are user-specific

2. **Firestore Query Failed**
   ```typescript
   // Check browser console
   // Look for query errors
   ```

3. **Clear Cache and Reload**
   ```bash
   # Browser
   Ctrl+Shift+R (hard reload)
   ```

### Delete Doesn't Work

**Problem**: Conversation won't delete

**Solutions**:

1. **Check Firestore Rules**
   ```javascript
   // Must allow delete for userId
   allow delete: if request.auth.uid == resource.data.userId;
   ```

2. **Check Console**
   ```typescript
   // Look for mutation errors
   ```

## Performance Issues

### Slow Response Times

**Problem**: AI takes too long to respond

**Solutions**:

1. **Use Faster Model**
   ```bash
   # backend/.env
   LLM_MODEL=gpt-3.5-turbo  # Instead of gpt-4
   ```

2. **Reduce Context**
   ```bash
   TOP_K_RESULTS=3  # Fewer chunks
   MAX_CONTEXT_LENGTH=2000  # Shorter context
   ```

3. **Check Network**
   - Test internet speed
   - Check API service status

### High Memory Usage

**Problem**: Application uses too much RAM

**Solutions**:

1. **Limit ChromaDB Cache**
   ```bash
   CHROMA_CACHE_SIZE=500
   ```

2. **Reduce Chunk Size**
   ```bash
   CHUNK_SIZE=500
   ```

3. **Clear Browser Cache**
   - Especially for large conversations

## Development Issues

### Hot Reload Not Working

**Frontend:**
```bash
# Kill all Next.js processes
pkill -f "next dev"

# Clear .next cache
rm -rf .next

# Restart
npm run dev
```

**Backend:**
```bash
# Ensure --reload flag is used
uvicorn main:app --reload
```

### TypeScript Errors

**Problem**: Type errors in frontend

**Solutions**:

1. **Regenerate Types**
   ```bash
   npm run build
   ```

2. **Check tsconfig.json**
   ```json
   {
     "compilerOptions": {
       "strict": true,
       "paths": {
         "@/*": ["./*"]
       }
     }
   }
   ```

### Import Errors

**Problem**: Module not found

**Solutions**:

1. **Check Import Path**
   ```typescript
   // Use @ alias
   import { Component } from "@/components/Component";
   ```

2. **Restart Dev Server**
   ```bash
   # Kill and restart
   ```

## Docker Issues

### Container Won't Start

**Problem**: `docker-compose up` fails

**Solutions**:

1. **Check Logs**
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Rebuild Images**
   ```bash
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Check Ports**
   ```bash
   # Ports 3000 and 8000 must be free
   lsof -i :3000
   lsof -i :8000
   ```

### Volume Issues

**Problem**: Data not persisting

**Solutions**:

1. **Check docker-compose.yml**
   ```yaml
   volumes:
     - ./backend/chroma_db:/data
   ```

2. **Permissions**
   ```bash
   chmod -R 755 backend/chroma_db
   ```

## Testing Issues

### Tests Failing

**Backend:**
```bash
# Clear pytest cache
rm -rf .pytest_cache
pytest -v
```

**Frontend:**
```bash
# Clear vitest cache
rm -rf node_modules/.vitest
npm test
```

### Coverage Not Generated

**Solutions**:

1. **Install Coverage Tools**
   ```bash
   # Backend
   poetry add --group dev pytest-cov
   
   # Frontend
   npm install --save-dev @vitest/coverage-v8
   ```

2. **Run with Coverage Flag**
   ```bash
   # Backend
   pytest --cov=app --cov-report=html
   
   # Frontend
   npm run test:coverage
   ```

## Environment Issues

### Environment Variables Not Loading

**Problem**: Config values are undefined

**Solutions**:

1. **Check File Name**
   - Backend: `.env` (no .local)
   - Frontend: `.env.local`

2. **Check Prefix**
   ```bash
   # Frontend vars must start with NEXT_PUBLIC_
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Restart Server**
   ```bash
   # Changes require restart
   ```

### API Keys Not Working

**Problem**: Authentication errors from OpenAI/Firebase

**Solutions**:

1. **Verify Key Format**
   ```bash
   # OpenAI keys start with sk-
   LLM_API_KEY=sk-proj-...
   
   # Firebase keys are alphanumeric
   NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
   ```

2. **Check Key Permissions**
   - OpenAI: Verify key has correct permissions
   - Firebase: Check project settings

3. **Regenerate Keys**
   - Create new API key
   - Update .env files

## Still Having Issues?

### 1. Check Logs

**Backend:**
```bash
# Terminal where backend is running
# Look for error messages
```

**Frontend:**
```bash
# Browser Console (F12)
# Check Console and Network tabs
```

### 2. Enable Debug Mode

**Backend:**
```bash
# backend/.env
LOG_LEVEL=DEBUG
```

**Frontend:**
```typescript
// Add debug logs
console.log('Debug:', variable);
```

### 3. Search Issues

- [GitHub Issues](https://github.com/andrea-ragalzi/document-intelligent-hub/issues)
- Search for similar problems

### 4. Create Issue

If problem persists:

1. Go to [GitHub Issues](https://github.com/andrea-ragalzi/document-intelligent-hub/issues/new)
2. Provide:
   - Error message
   - Steps to reproduce
   - Environment (OS, versions)
   - Logs

## Related Pages

- [Installation Guide](Installation-Guide)
- [Configuration](Configuration)
- [FAQ](FAQ)
- [Development Workflow](Development-Workflow)
