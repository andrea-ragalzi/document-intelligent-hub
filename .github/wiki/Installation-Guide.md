# Installation Guide

This guide will help you set up the Document Intelligent Hub on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: v18.0.0 or higher
- **Python**: 3.9 or higher
- **Poetry**: Python dependency management
- **Git**: Version control
- **Docker** (optional): For containerized deployment

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/andrea-ragalzi/document-intelligent-hub.git
cd document-intelligent-hub
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend
poetry install
```

#### Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# LLM Provider (OpenAI, Anthropic, etc.)
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# CORS
FRONTEND_URL=http://localhost:3000
```

#### Start the Backend Server

```bash
poetry run uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### 3. Frontend Setup

#### Install Node Dependencies

```bash
cd ../frontend
npm install
```

#### Configure Environment Variables

Create a `.env.local` file in the `frontend` directory:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Firebase configuration:

```env
# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Start the Frontend Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 4. Verify Installation

### Backend Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Frontend Access

Open your browser and navigate to:
```
http://localhost:3000
```

You should see the login page.

## 5. Firebase Setup

### Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable **Authentication** (Email/Password)
4. Enable **Firestore Database**

### Firestore Security Rules

In Firebase Console, set up security rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /conversations/{conversationId} {
      allow read, write: if request.auth != null && 
                          request.auth.uid == resource.data.userId;
      allow create: if request.auth != null && 
                       request.auth.uid == request.resource.data.userId;
    }
  }
}
```

### Get Firebase Config

1. Go to Project Settings → General
2. Scroll to "Your apps" → Web app
3. Copy the configuration object
4. Add values to `frontend/.env.local`

## Docker Installation (Alternative)

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Troubleshooting

### Port Already in Use

If port 3000 or 8000 is already in use:

**Frontend:**
```bash
PORT=3001 npm run dev
```

**Backend:**
```bash
uvicorn main:app --reload --port 8001
```

### Module Not Found Errors

**Frontend:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Backend:**
```bash
poetry install --no-root
```

### Firebase Connection Issues

1. Verify `.env.local` has correct Firebase config
2. Check Firebase project is in production mode
3. Verify security rules are published

### ChromaDB Errors

```bash
# Delete existing database
rm -rf backend/chroma_db

# Restart backend
poetry run uvicorn main:app --reload
```

## Next Steps

- [Quick Start Guide](Quick-Start) - Learn basic usage
- [Configuration](Configuration) - Advanced configuration options
- [Development Workflow](Development-Workflow) - Start developing

## Getting Help

- [Common Issues](Common-Issues)
- [FAQ](FAQ)
- [GitHub Issues](https://github.com/andrea-ragalzi/document-intelligent-hub/issues)
