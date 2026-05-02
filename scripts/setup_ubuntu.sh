#!/usr/bin/env bash
# =============================================================================
# DNS One — setup en Ubuntu 22.04+
# Instala: Docker Engine, Docker Compose plugin, Git, dependencias.
# Uso:
#   sudo bash scripts/setup_ubuntu.sh
# =============================================================================
set -euo pipefail

# --- Verificar que estamos en Ubuntu ---
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
  echo "⚠  Este script está pensado para Ubuntu 22.04+."
  echo "   Detectado: $(. /etc/os-release && echo "${PRETTY_NAME:-desconocido}")"
  read -rp "¿Continuar de todos modos? [y/N] " yn
  [[ "$yn" =~ ^[Yy]$ ]] || exit 1
fi

# --- Requiere sudo/root ---
if [[ $EUID -ne 0 ]]; then
  echo "❌ Este script requiere sudo: 'sudo bash scripts/setup_ubuntu.sh'"
  exit 1
fi

echo "==[ DNS One — setup Ubuntu ]=="

# --- 1. Actualizar paquetes base ---
echo "→ apt update & upgrade..."
apt-get update -y
apt-get upgrade -y

# --- 2. Dependencias generales ---
echo "→ Instalando paquetes base..."
apt-get install -y \
  ca-certificates curl gnupg lsb-release \
  git make jq htop \
  build-essential

# --- 3. Docker Engine + Compose plugin ---
if ! command -v docker >/dev/null 2>&1; then
  echo "→ Instalando Docker Engine..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  systemctl enable --now docker
else
  echo "→ Docker ya instalado: $(docker --version)"
fi

# --- 4. Verificación de versiones ---
echo
echo "==[ Verificando versiones ]=="
docker --version || { echo "❌ docker no disponible"; exit 1; }
docker compose version || { echo "❌ docker compose plugin no disponible"; exit 1; }
git --version

# --- 5. Permisos para usuario no-root ---
INVOKER="${SUDO_USER:-}"
if [[ -n "$INVOKER" && "$INVOKER" != "root" ]]; then
  echo "→ Agregando '$INVOKER' al grupo docker (cierra sesión y vuelve a entrar para aplicar)"
  usermod -aG docker "$INVOKER" || true
fi

# --- 6. Habilitar firewall básico (opcional) ---
if command -v ufw >/dev/null 2>&1; then
  echo "→ ufw detectado. Si el servidor es público, recuerda permitir 22/tcp y los puertos de la app."
fi

echo
echo "✅ Setup completo."
echo
echo "Siguientes pasos:"
echo "  1. cp .env.example .env  (y editar valores reales)"
echo "  2. bash scripts/start.sh"
echo "  3. bash scripts/healthcheck.sh"
