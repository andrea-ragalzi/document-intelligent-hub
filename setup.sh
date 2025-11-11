#!/bin/bash

# 🚀 Document Intelligent Hub - Setup Script
# Automates the initial setup and deployment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}==================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main script
print_header "Document Intelligent Hub - Setup"

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

if ! command_exists docker-compose; then
    print_warning "docker-compose command not found, trying docker compose..."
    if ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi
print_success "Docker Compose is available"

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
        
        # Prompt for OpenAI API key
        echo ""
        print_info "Please enter your OpenAI API Key:"
        print_info "(Get one at: https://platform.openai.com/api-keys)"
        read -p "API Key: " api_key
        
        if [ -z "$api_key" ]; then
            print_error "API key cannot be empty"
            exit 1
        fi
        
        # Update .env file
        sed -i.bak "s/your-openai-api-key-here/$api_key/" .env && rm .env.bak
        print_success "API key configured"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_success ".env file exists"
    
    # Check if API key is configured
    if grep -q "your-openai-api-key-here" .env; then
        print_warning "OpenAI API key not configured in .env"
        print_info "Please edit .env and add your API key"
        exit 1
    fi
fi

# Choose deployment mode
echo ""
print_info "Select deployment mode:"
echo "1) Development (with hot reload)"
echo "2) Production"
read -p "Enter choice [1-2]: " mode_choice

if [ "$mode_choice" == "1" ]; then
    MODE="development"
    print_info "Development mode selected"
else
    MODE="production"
    print_info "Production mode selected"
fi

# Build and start services
print_header "Building and Starting Services"

print_info "This may take several minutes on first run..."
echo ""

if [ "$MODE" == "development" ]; then
    $DOCKER_COMPOSE up -d --build
else
    $DOCKER_COMPOSE -f docker-compose.yml up -d --build
fi

# Wait for services to be healthy
print_info "Waiting for services to start..."
sleep 10

# Check service status
print_header "Service Status"

if $DOCKER_COMPOSE ps | grep -q "Up"; then
    print_success "Services are running"
    
    echo ""
    print_info "Backend API: http://localhost:8000"
    print_info "API Docs:    http://localhost:8000/docs"
    print_info "Frontend:    http://localhost:3000"
    echo ""
    
    # Show logs tail
    print_info "Recent logs:"
    echo ""
    $DOCKER_COMPOSE logs --tail=20
    
    echo ""
    print_success "Setup complete! 🎉"
    echo ""
    print_info "Useful commands:"
    echo "  View logs:        $DOCKER_COMPOSE logs -f"
    echo "  Stop services:    $DOCKER_COMPOSE stop"
    echo "  Restart services: $DOCKER_COMPOSE restart"
    echo "  Remove all:       $DOCKER_COMPOSE down -v"
    echo ""
    
else
    print_error "Services failed to start"
    print_info "Check logs with: $DOCKER_COMPOSE logs"
    exit 1
fi
