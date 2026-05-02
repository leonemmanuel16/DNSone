#!/usr/bin/env bash
# =============================================================================
# DNS One — arranque local con Docker Compose.
# - Construye imágenes
# - Levanta db, backend, frontend
# - Aplica migraciones Alembic
# - Corre el seed de admin/roles/permisos (idempotente)
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    echo "⚠  No existe .env. Copiando desde .env.example."
    cp .env.example .env
    echo "→ Edita .env antes de seguir (JWT_SECRET_KEY, ADMIN_PASSWORD, etc)."
    exit 1
  else
    echo "❌ No existe .env ni .env.example."
    exit 1
  fi
fi

echo "==[ Levantando DNS One ]=="
docker compose up -d --build

echo "→ Esperando a que la DB esté lista..."
for _ in {1..30}; do
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER:-dnsone}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "→ Aplicando migraciones..."
docker compose exec -T backend alembic upgrade head

echo "→ Ejecutando seed inicial..."
docker compose exec -T backend python -m app.scripts.seed

echo
echo "✅ DNS One levantado."
echo "   Backend (Swagger): http://localhost:8000/docs"
echo "   Frontend:          http://localhost:3000"
echo "   Health:            http://localhost:8000/health"
