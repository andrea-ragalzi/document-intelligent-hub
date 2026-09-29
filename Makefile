.PHONY: help build build-frontend build-backend up down restart logs test clean prune

# Default target
help:
	@echo "🧠 Document Intelligent Hub - Available Commands"
	@echo ""
	@echo "Setup & Deployment:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo ""
	@echo "Development:"
	@echo "  make dev-backend  - Start backend in development mode"
	@echo "  make dev-frontend - Start frontend in development mode"
	@echo "  make logs         - View all logs"
	@echo "  make logs-backend - View backend logs only"
	@echo "  make logs-frontend - View frontend logs only"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run backend tests in the Compose service"
	@echo "  make test-coverage - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make quality      - Required local, agent and CI quality gates"
	@echo "  make lint-frontend - Run ESLint on frontend"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Remove containers (keeps volumes)"
	@echo "  make prune      - Remove containers and volumes (⚠️  deletes data)"
	@echo "  make shell-backend  - Access backend container shell"
	@echo "  make shell-frontend - Access frontend container shell"
	@echo ""

# Build images
# Frontend requires NEXT_PUBLIC_* vars from frontend/.env.local at build time.
# docker compose --env-file passes them for build arg substitution without touching runtime env.
build:
	@echo "🔨 Building backend image..."
	docker compose build --no-cache backend
	@echo "🔨 Building frontend image (with Firebase config)..."
	docker compose --env-file frontend/.env.local build --no-cache frontend

build-frontend:
	@echo "🔨 Building frontend image (with Firebase config)..."
	docker compose --env-file frontend/.env.local build --no-cache frontend

build-backend:
	@echo "🔨 Building backend image..."
	docker compose build --no-cache backend

# Start services
up:
	@echo "▶️  Starting services..."
	docker compose up -d
	@echo "✅ Services started"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

# Stop services
down:
	@echo "⏸️  Stopping services..."
	docker compose down
	@echo "✅ Services stopped"

# Restart services
restart:
	@echo "🔄 Restarting services..."
	docker compose restart
	@echo "✅ Services restarted"

# View logs
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

# Development mode (with hot reload)
dev-backend:
	@echo "🔧 Starting backend in development mode..."
	@echo "   Backend will be accessible at: http://0.0.0.0:8000"
	@echo "   Use your local IP for mobile access"
	cd backend && poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "🔧 Starting frontend in development mode..."
	cd frontend && npm run dev

# Testing
test:
	@echo "🧪 Running backend tests..."
	docker compose exec backend pytest tests/ -v

test-coverage:
	@echo "🧪 Running tests with coverage..."
	docker compose exec backend pytest --cov=app --cov-report=html --cov-report=term
	@echo "📊 Coverage report: backend/htmlcov/index.html"

# Shell access
shell-backend:
	@echo "🐚 Accessing backend container..."
	docker compose exec backend sh

shell-frontend:
	@echo "🐚 Accessing frontend container..."
	docker compose exec frontend sh

# Cleanup
clean:
	@echo "🧹 Cleaning up containers..."
	docker compose down
	@echo "✅ Containers removed (volumes preserved)"

prune:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		echo "✅ All containers and volumes removed"; \
	else \
		echo "❌ Cancelled"; \
	fi

# Status check
status:
	@echo "📊 Service Status:"
	@docker compose ps

# Health check
health:
	@echo "🏥 Checking service health..."
	@echo -n "Backend: "
	@curl -sf http://localhost:8000/ > /dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo -n "Frontend: "
	@curl -sf http://localhost:3000/ > /dev/null && echo "✅ Healthy" || echo "❌ Unhealthy"

# Install dependencies (local development)
install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && poetry install --no-root

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm ci

# Format code
format-backend:
	@echo "✨ Formatting backend code..."
	cd backend && black app/ tests/

lint-frontend:
	@echo "🔍 Linting frontend code..."
	cd frontend && npm run lint

# Canonical quality gates. CI uses these same area targets without repeating tests.
.PHONY: quality quality-backend quality-frontend quality-tooling
quality: quality-tooling quality-backend quality-frontend

quality-tooling:
	python3 -m unittest discover -s quality -p 'test_*.py'

quality-backend:
	python3 quality/check_size.py backend
	cd backend && poetry run ruff check app main.py tests ../quality
	cd backend && poetry run mypy --config-file=mypy.ini app/ --strict --pretty
	cd backend && find app -name '*.py' -print0 | xargs -0 poetry run pylint --rcfile=.pylintrc --fail-under=9.0 --fail-on=E,F
	cd backend && poetry run lizard app/ -l python -C 25 -T nloc=200 -w
	cd backend && poetry run pytest --cov=app --cov-report=xml --cov-report=term

quality-frontend:
	python3 quality/check_size.py frontend
	cd frontend && node --test ../quality/test_frontend_boundaries.mjs
	cd frontend && npm run quality:check
	cd frontend && npm run build
