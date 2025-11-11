# 🐳 Docker Deployment Guide

Complete guide for deploying Document Intelligent Hub using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+ 
- Docker Compose v2.0+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
- At least 4GB RAM available
- 10GB free disk space

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd document-intelligent-hub
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

**Required:** Set your `OPENAI_API_KEY` in `.env`:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Build and Start Services

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐
│   Frontend      │─────▶│   Backend       │
│   (Next.js)     │      │   (FastAPI)     │
│   Port: 3000    │      │   Port: 8000    │
└─────────────────┘      └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │   ChromaDB      │
                         │   (Volume)      │
                         └─────────────────┘
```

## 📦 Services

### Backend (FastAPI)
- **Image**: Custom built from `./backend/Dockerfile`
- **Port**: 8000
- **Volume**: `chroma_data` (persists vector database)
- **Health Check**: HTTP GET to `/`

### Frontend (Next.js)
- **Image**: Custom built from `./frontend/Dockerfile`
- **Port**: 3000
- **Depends On**: Backend service
- **Health Check**: HTTP GET to root

## 🔧 Configuration

### Environment Variables

#### Backend (`backend/.env`)
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
CHROMA_DB_PATH=/app/chroma_db
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-3.5-turbo
APP_NAME=Document Intelligent Hub
```

#### Frontend
```env
# API endpoint (for Docker)
NEXT_PUBLIC_API_BASE_URL=http://backend:8000/rag

# For local development (without Docker)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/rag
```

### Port Customization

Edit `docker-compose.yml` to change ports:
```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Host:Container
  frontend:
    ports:
      - "3001:3000"  # Host:Container
```

## 🛠️ Common Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services
```bash
# Stop (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose up -d --build backend

# Rebuild all services
docker-compose up -d --build
```

### Access Container Shell
```bash
# Backend
docker-compose exec backend sh

# Frontend
docker-compose exec frontend sh
```

## 🔍 Troubleshooting

### Problem: Services won't start

**Check logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Common causes:**
- Missing `OPENAI_API_KEY` in `.env`
- Ports 3000 or 8000 already in use
- Insufficient system resources

### Problem: Frontend can't connect to backend

**Check network:**
```bash
docker network inspect document-intelligent-hub_app-network
```

**Verify environment variable:**
```bash
docker-compose exec frontend env | grep API_BASE_URL
```

Should show: `NEXT_PUBLIC_API_BASE_URL=http://backend:8000/rag`

### Problem: ChromaDB data lost after restart

**Check volume:**
```bash
docker volume ls | grep chroma
docker volume inspect document-intelligent-hub_chroma_data
```

**Ensure using named volume:**
```yaml
volumes:
  chroma_data:
```

### Problem: Permission denied errors

**Fix ownership (Linux/Mac):**
```bash
sudo chown -R $USER:$USER ./backend/chroma_db
sudo chown -R $USER:$USER ./backend/uploads
```

### Problem: Out of memory

**Increase Docker memory:**
- Docker Desktop: Settings → Resources → Memory (increase to 4GB+)
- Linux: Edit `/etc/docker/daemon.json`

### Problem: Health check failing

**Test manually:**
```bash
# Backend
curl http://localhost:8000/

# Frontend  
curl http://localhost:3000/
```

## 🧪 Running Tests

### Backend Tests
```bash
# Inside container
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Specific test file
docker-compose exec backend pytest tests/test_rag_endpoints.py
```

### Build Test Image
```bash
# Build and run tests
docker build -t document-hub-backend-test -f backend/Dockerfile backend/
docker run --rm document-hub-backend-test pytest
```

## 📊 Monitoring

### Resource Usage
```bash
# Real-time stats
docker stats

# Specific containers
docker stats document-hub-backend document-hub-frontend
```

### Disk Usage
```bash
# All Docker resources
docker system df

# Detailed view
docker system df -v
```

## 🧹 Cleanup

### Remove Unused Resources
```bash
# Remove stopped containers, unused networks, dangling images
docker system prune

# Also remove volumes (⚠️ deletes data)
docker system prune -a --volumes
```

### Remove Project Completely
```bash
# Stop and remove everything
docker-compose down -v --rmi all

# Remove volumes manually
docker volume rm document-intelligent-hub_chroma_data
```

## 🚢 Production Deployment

### Using Docker Compose on VPS

1. **Clone repository on server:**
```bash
ssh user@your-server.com
git clone <repo-url>
cd document-intelligent-hub
```

2. **Configure environment:**
```bash
cp .env.example .env
nano .env  # Add production API keys
```

3. **Start services:**
```bash
docker-compose up -d --build
```

4. **Setup reverse proxy (Nginx example):**
```nginx
# /etc/nginx/sites-available/document-hub
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **Enable SSL with Let's Encrypt:**
```bash
sudo certbot --nginx -d your-domain.com
```

### Environment-Specific Configs

**Development:**
```yaml
# docker-compose.dev.yml
services:
  backend:
    volumes:
      - ./backend:/app  # Hot reload
    environment:
      - DEBUG=true
```

**Production:**
```yaml
# docker-compose.prod.yml
services:
  backend:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Run with specific config:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔒 Security Best Practices

1. **Never commit `.env` files**
   - Add to `.gitignore`
   - Use secrets management in production

2. **Use non-root users**
   - Both Dockerfiles already implement this

3. **Limit resource usage**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

4. **Regular updates**
```bash
# Update base images
docker-compose pull
docker-compose up -d --build
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Docker](https://nextjs.org/docs/deployment#docker-image)

## 🆘 Support

If you encounter issues:
1. Check logs: `docker-compose logs`
2. Verify environment variables
3. Ensure all prerequisites are met
4. Check GitHub Issues
5. Create a new issue with logs and system info

---

**Happy Deploying! 🚀**
