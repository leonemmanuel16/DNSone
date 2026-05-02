#!/usr/bin/env bash
# =============================================================================
# DNS One — healthcheck de servicios.
# Verifica que API, DB y Frontend respondan.
# Salida con código distinto de 0 si algún servicio falla.
# =============================================================================
set -uo pipefail

API_URL="${API_URL:-http://localhost:8000}"
FRONT_URL="${FRONT_URL:-http://localhost:3000}"

ok=0
fail=0

check() {
  local name="$1" url="$2" expected="${3:-200}"
  local code
  code=$(curl -fsS -o /dev/null -w "%{http_code}" --max-time 5 "$url" || echo "000")
  if [[ "$code" == "$expected" ]]; then
    echo "✅ $name → $code ($url)"
    ((ok++))
  else
    echo "❌ $name → $code ($url)"
    ((fail++))
  fi
}

echo "==[ Healthcheck DNS One ]=="
check "API /health"   "$API_URL/health"           200
check "API /docs"     "$API_URL/docs"             200
check "API openapi"   "$API_URL/openapi.json"     200
check "Frontend"      "$FRONT_URL"                200

# Postgres vía docker compose
if command -v docker >/dev/null 2>&1; then
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER:-dnsone}" >/dev/null 2>&1; then
    echo "✅ Postgres → ready"
    ((ok++))
  else
    echo "❌ Postgres → not ready"
    ((fail++))
  fi
fi

echo
echo "Resumen: $ok OK · $fail FAIL"
exit $((fail > 0 ? 1 : 0))
