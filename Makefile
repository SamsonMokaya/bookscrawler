.PHONY: help build up down logs restart clean test shell

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View logs from all services"
	@echo "  make restart  - Restart all services"
	@echo "  make clean    - Remove all containers and volumes"
	@echo "  make shell    - Access backend container shell"
	@echo "  make test     - Run tests"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -f

shell:
	docker exec -it bookscrawler_backend /bin/bash

test:
	docker exec -it bookscrawler_backend pytest

# Development commands
dev-up:
	docker-compose up

dev-rebuild:
	docker-compose up --build

# Monitor specific services
logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f celery_worker

logs-beat:
	docker-compose logs -f celery_beat

# Celery commands
celery-status:
	docker exec -it bookscrawler_celery_worker celery -A app.celery_app.celery_app status

celery-inspect:
	docker exec -it bookscrawler_celery_worker celery -A app.celery_app.celery_app inspect active

celery-purge:
	docker exec -it bookscrawler_celery_worker celery -A app.celery_app.celery_app purge

