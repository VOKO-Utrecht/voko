.PHONY: help setup build up down restart logs logs-web logs-db shell db-shell clean test migrate superuser runserver validate reset

# Default target
help:
	@echo "VOKO Development Environment"
	@echo "============================"
	@echo "Available commands:"
	@echo "  setup      - Complete setup of development environment (recommended)"
	@echo "  build      - Build Docker images"
	@echo "  up         - Start all services"
	@echo "  down       - Stop all services"
	@echo "  restart    - Restart all services"
	@echo "  logs       - View all logs"
	@echo "  logs-web   - View web application logs"
	@echo "  logs-db    - View database logs"
	@echo "  shell      - Access web container shell"
	@echo "  db-shell   - Access database shell"
	@echo "  clean      - Clean up containers and volumes"
	@echo "  test       - Run tests"
	@echo "  migrate    - Run database migrations"
	@echo "  superuser  - Create Django superuser"
	@echo "  validate   - Validate setup is working correctly"
	@echo "  reset      - Reset database (WARNING: deletes all data)"

# Complete setup - simplified one-command setup
setup:
	@echo "Starting VOKO development environment..."
	@echo "This will build and start all services with automatic setup."
	docker-compose up --build

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# View web logs
logs-web:
	docker-compose logs -f web

# View database logs
logs-db:
	docker-compose logs -f db

# Access web container shell
shell:
	docker exec -it voko_web bash

# Access database shell
db-shell:
	docker exec -it voko_db psql -U postgres

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Run tests
test:
	docker exec voko_web uv run python manage.py test --settings=vokou.settings.testing

# Run migrations
migrate:
	docker exec voko_web uv run python manage.py makemigrations --settings=vokou.settings.development
	docker exec voko_web uv run python manage.py migrate --settings=vokou.settings.development

# Create superuser
superuser:
	docker exec -it voko_web uv run python manage.py createsuperuser --noinput --settings=vokou.settings.development

# Run crons
crons:
	docker exec voko_web uv run python manage.py runcrons --settings=vokou.settings.development

# Start development server (if not using docker-compose)
runserver:
	docker exec voko_web uv run python manage.py runserver 0.0.0.0:8000 --settings=vokou.settings.development

# Reset database (WARNING: deletes all data)
reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up --build; \
	else \
		echo "Reset cancelled."; \
	fi

# Flush sqlite database (if using sqlite)
flush:
	@echo "Flushing SQLite database..."
	uv run python webapp/manage.py flush --no-input --settings=vokou.settings.development

flush-docker:
	@echo "Flushing SQLite database in Docker..."
	docker exec voko_web uv run python manage.py flush --no-input --settings=vokou.settings.development

# start webapp
start-webapp:
	@echo "Starting web application..."
	uv run python webapp/manage.py runserver --settings=vokou.settings.development