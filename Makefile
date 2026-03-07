.PHONY: help setup build up down restart logs logs-web logs-db shell db-shell clean test migrate superuser runserver validate reset

# Default target
help:
	@echo "VOKO Development Environment"
	@echo "============================"
	@echo "Available commands:"
	@echo ""
	@echo "Docker commands:"
	@echo "  docker-setup     - Complete setup of development environment (recommended)"
	@echo "  docker-build     - Build Docker images"
	@echo "  docker-up        - Start all services"
	@echo "  docker-down      - Stop all services"
	@echo "  docker-clean     - Clean up containers and volumes"
	@echo "  docker-flush     - Flush SQLite database in Docker"
	@echo "  docker-migrate   - Run database migrations in Docker"
	@echo "  docker-superuser - Create Django superuser in Docker"
	@echo "  docker-runcrons  - Run crons in Docker"
	@echo "  docker-runserver - Start development server in Docker"
	@echo "  docker-test      - Run tests in Docker"
	@echo "  docker-reset     - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Local development commands:"
	@echo "  migrate          - Make and run database migrations locally"
	@echo "  create-superuser - Create Django superuser locally"
	@echo "  run-crons        - Run crons locally"
	@echo "  test             - Run tests locally"
	@echo "  start-webapp     - Start web application locally"
	@echo "  flush            - Flush SQLite database locally"

# Complete setup - simplified one-command setup
docker-setup:
	@echo "Starting VOKO development environment..."
	@echo "This will build and start all services with automatic setup."
	docker-compose up --build

# Build Docker images
docker-build:
	docker-compose build

# Start services
docker-up:
	docker-compose up -d

# Stop services
docker-down:
	docker-compose down

# Clean up
docker-clean:
	docker-compose down -v
	docker system prune -f

# Flush database
docker-flush:
	@echo "Flushing SQLite database in Docker..."
	docker exec voko_web uv run python manage.py flush --no-input --settings=vokou.settings.development

# Run migrations
docker-migrate:
	docker exec voko_web uv run python manage.py makemigrations --settings=vokou.settings.development
	docker exec voko_web uv run python manage.py migrate --settings=vokou.settings.development

# Create superuser
docker-superuser:
	docker exec -it voko_web uv run python manage.py createsuperuser --noinput --settings=vokou.settings.development

# Run crons
docker-runcrons:
	docker exec voko_web uv run python manage.py runcrons --settings=vokou.settings.development

# Start development server (if not using docker-compose)
docker-runserver:
	docker exec voko_web uv run python manage.py runserver 0.0.0.0:8000 --settings=vokou.settings.development

# Run tests
docker-test:
	docker exec voko_web uv run pytest webapp/ --ds=vokou.settings.testing

# Reset database (WARNING: deletes all data)
docker-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up --build; \
	else \
		echo "Reset cancelled."; \
	fi

# make migrations
migrate:
	@echo "Making migrations..."
	uv run python webapp/manage.py makemigrations --settings=vokou.settings.development
	uv run python webapp/manage.py migrate --settings=vokou.settings.development

# create superuser
create-superuser:
	@echo "Creating superuser..."
	uv run python webapp/manage.py createsuperuser --noinput --settings=vokou.settings.development

# run crons
runcrons:
	@echo "Running crons..."
	uv run python webapp/manage.py runcrons --force --settings=vokou.settings.development
	
# test
test:
	@echo "Running tests..."
	uv run pytest webapp/ --ds=vokou.settings.testing 

# start webapp
start-webapp:
	@echo "Starting web application..."
	uv run python webapp/manage.py runserver --settings=vokou.settings.development

# Flush sqlite database
flush:
	@echo "Flushing SQLite database..."
	uv run python webapp/manage.py flush --no-input --settings=vokou.settings.development