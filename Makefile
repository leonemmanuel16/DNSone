# =============================================================================
# DNS One — Makefile (atajos de desarrollo)
# =============================================================================

.PHONY: help up down build logs restart \
        migrate makemigration seed \
        test lint format \
        shell-backend shell-db \
        clean

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Docker ----
up: ## Levantar todos los servicios
	docker compose up -d --build

down: ## Detener todos los servicios
	docker compose down

build: ## Reconstruir imágenes
	docker compose build

logs: ## Ver logs de todos los servicios
	docker compose logs -f

logs-backend: ## Ver logs del backend
	docker compose logs -f backend

logs-frontend: ## Ver logs del frontend
	docker compose logs -f frontend

restart: ## Reiniciar todos los servicios
	docker compose restart

# ---- Base de datos ----
migrate: ## Aplicar migraciones pendientes
	docker compose exec backend alembic upgrade head

makemigration: ## Crear nueva migración (uso: make makemigration m="descripcion")
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

seed: ## Cargar datos iniciales (admin, roles)
	docker compose exec backend python -m app.scripts.seed

db-reset: ## Borrar y recrear DB (¡destructivo!)
	docker compose down -v
	docker compose up -d db
	sleep 5
	docker compose up -d backend
	sleep 3
	$(MAKE) migrate
	$(MAKE) seed

# ---- Tests / Calidad ----
test: ## Correr tests del backend
	docker compose exec backend pytest -v

test-cov: ## Tests con cobertura
	docker compose exec backend pytest --cov=app --cov-report=term-missing

lint: ## Lint backend
	docker compose exec backend ruff check app/

format: ## Formatear código backend
	docker compose exec backend ruff format app/

# ---- Shells ----
shell-backend: ## Shell dentro del contenedor backend
	docker compose exec backend bash

shell-db: ## psql dentro del contenedor db
	docker compose exec db psql -U $${POSTGRES_USER:-dnsone} -d $${POSTGRES_DB:-dns_one}

# ---- Limpieza ----
clean: ## Borrar contenedores, volúmenes y caches locales
	docker compose down -v
	rm -rf backend/__pycache__ backend/.pytest_cache backend/.ruff_cache
	rm -rf frontend/.next frontend/node_modules
