# Quick Start Guide

Get started with Document Intelligent Hub in 5 minutes.

## Prerequisites

Ensure you have completed the [Installation Guide](Installation-Guide) first.

## Step 1: Start the Backend

```bash
cd backend
poetry run uvicorn main:app --reload
```

Backend will be available at: http://localhost:8000

## Step 2: Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Step 3: Create an Account

1. Open http://localhost:3000 in your browser
2. Click **"Sign Up"**
3. Enter your email and password
4. Click **"Create Account"**

## Step 4: Upload a Document

1. After logging in, you'll see the main interface
2. In the left sidebar, find the **"Upload Document"** section
3. Click **"Choose File"** or drag & drop a PDF
4. Click **"Upload"**
5. Wait for processing to complete

**Supported formats:**
- ✅ PDF documents
- 📄 Text content extraction
- 🌐 Multi-language support

## Step 5: Chat with Your Document

1. Once the document is uploaded, type a question in the chat input
2. Example: *"What is the main topic of this document?"*
3. Press **Enter** or click the send button
4. Watch the AI stream its response in real-time

**Features:**
- 🔄 Streaming responses
- 📚 Context from your documents
- 💡 Source citations
- 🌍 Italian/English support

## Step 6: Save Your Conversation

Conversations are **automatically saved** after each response:
- ✅ Auto-save every 500ms after assistant finishes
- 💾 Stored in Firebase Firestore
- 📱 Access from any device
- 🔒 Private to your account

## Step 7: Load Previous Conversations

1. Look at the **"Saved Conversations"** section in the sidebar
2. Click the **blue book icon** to load a conversation
3. The chat history will be restored instantly
4. Continue the conversation or start a new one

## Common Tasks

### Rename a Conversation

1. Find the conversation in the sidebar
2. Click the **green edit icon**
3. Type the new name
4. Press **Enter** or click **"Rename"**

### Delete a Conversation

1. Find the conversation in the sidebar
2. Click the **red trash icon**
3. Confirm deletion in the modal
4. The conversation will be removed

### Start a New Conversation

1. Click the **"Nuova"** button in the chat header
2. The current chat will be cleared
3. Start typing to begin a new conversation

### Toggle Dark Mode

1. Click the **sun/moon icon** in the top-right corner
2. Theme preference is saved automatically
3. Works across all pages

## Example Workflow

### Document Analysis Workflow

```
1. Upload → research-paper.pdf
2. Ask → "Summarize the key findings"
3. Ask → "What methodology was used?"
4. Ask → "What are the limitations?"
5. Save → Conversation auto-saved as "Summarize the key findings..."
```

### Multi-Document Q&A

```
1. Upload → document1.pdf (financial report)
2. Ask questions about document1
3. Upload → document2.pdf (market analysis)  
4. Ask questions that combine both documents
5. System retrieves relevant context from both
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in input |
| `Ctrl/Cmd + K` | Focus on chat input |
| `Esc` | Close modal |

## Tips & Tricks

### 1. Better Questions Get Better Answers

❌ **Bad**: "Tell me about it"  
✅ **Good**: "What are the main conclusions about climate change in section 3?"

### 2. Use Specific References

❌ **Bad**: "What does it say?"  
✅ **Good**: "According to the introduction, what is the research objective?"

### 3. Follow-up Questions Work Great

```
You: "Summarize the methodology"
AI: [Provides summary]
You: "What were the sample size details?"
AI: [Provides specific details]
```

### 4. Multi-turn Conversations

The system maintains context, so you can:
- Ask clarifying questions
- Request elaboration
- Compare different sections
- Ask for examples

## Troubleshooting

### Document Upload Fails

**Solution:**
- Check file is PDF format
- Ensure file size is reasonable (< 50MB)
- Verify backend is running

### No Response from Chat

**Solution:**
- Check backend is running (`http://localhost:8000/health`)
- Verify document was uploaded successfully
- Check browser console for errors

### Conversation Not Saving

**Solution:**
- Ensure you're logged in
- Check Firebase connection in console
- Wait for auto-save (500ms after AI finishes)

### Can't See Previous Conversations

**Solution:**
- Ensure you're logged in with the same account
- Check Firestore rules are published
- Refresh the page

## Next Steps

Now that you're up and running:

- [Configuration](Configuration) - Customize your setup
- [RAG Chat System](RAG-Chat-System) - How it works under the hood
- [API Endpoints](API-Endpoints) - Build custom integrations
- [Development Workflow](Development-Workflow) - Start developing

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/andrea-ragalzi/document-intelligent-hub/issues)
- **Wiki**: [Full Documentation](https://github.com/andrea-ragalzi/document-intelligent-hub/wiki)
- **FAQ**: [Common Questions](FAQ)

---

**Ready to dive deeper?** Check out the [Configuration Guide](Configuration) to customize your installation.
