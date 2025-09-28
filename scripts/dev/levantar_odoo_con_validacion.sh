#!/bin/bash
# Levantar Odoo 17 + módulo con validación, tests y verificación HTTP
# Versión mejorada – Inmoser DevOps

set -euo pipefail

# Configuración
ODOO_DB="${ODOO_DB:-inmoser17}"
ODOO_USER="${ODOO_USER:-odoo}"
ODOO_PASS="${ODOO_PASS:-odoo}"
ODOO_PORT="${ODOO_PORT:-8069}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASS="${ADMIN_PASS:-admin}"
NETWORK="inmoser-net"
ODOO_IMG="odoo:17"
PG_IMG="postgres:15"
ADDONS_HOST="$HOME/odoo-inmoser_clean/addons"
MODULO="inmoser_service_order"
LOGDIR="$HOME/odoo-inmoser_clean/logs"
CHANGELOG="$LOGDIR/changelog.txt"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOGDIR"

echo "🔍 Validando módulo antes de desplegar..."
if ! "$HOME/odoo-inmoser_clean/scripts/dev/simular_instalacion_odoo.sh" "$ADDONS_HOST/$MODULO"; then
  echo "❌ Módulo con errores. Abortando." | tee -a "$CHANGELOG"
  exit 1
fi

echo "🔌 Cerrando conexiones en puertos 5432, 8069 y 8070..."
for port in 5432 8069 8070; do
  pids=$(lsof -ti tcp:$port)
  if [ -n "$pids" ]; then
    echo "Matando procesos que usan el puerto $port: $pids"
    kill -9 $pids || true
  else
    echo "No hay procesos en el puerto $port"
  fi
done

echo "🧹 Limpiando todos los contenedores, volúmenes y redes Docker..."
docker stop $(docker ps -q) 2>/dev/null || true
docker rm -f $(docker ps -a -q) 2>/dev/null || true
docker volume prune -f
docker network prune -f

echo "Creando/red de Docker si no existe..."
docker network inspect "$NETWORK" &>/dev/null || docker network create "$NETWORK"

echo "Iniciando PostgreSQL..."
docker run -d --name inmoser-db \
  --network "$NETWORK" \
  -v inmoser-db-data:/var/lib/postgresql/data \
  -e POSTGRES_DB="$ODOO_DB" \
  -e POSTGRES_USER="$ODOO_USER" \
  -e POSTGRES_PASSWORD="$ODOO_PASS" \
  -p 127.0.0.1:$DB_PORT:5432 \
  "$PG_IMG"

TRIES=0
MAX_TRIES=15
SLEEP_INTERVAL=1
echo "⏳ Esperando a PostgreSQL..."
until docker exec inmoser-db pg_isready -U "$ODOO_USER" >/dev/null 2>&1; do
  ((TRIES++))
  if [[ $TRIES -gt $MAX_TRIES ]]; then
    echo "[ERROR] PostgreSQL no arrancó a tiempo"
    docker logs inmoser-db
    exit 1
  fi
  echo "Esperando PostgreSQL... ($TRIES/$MAX_TRIES)"
  sleep $SLEEP_INTERVAL
done
echo "PostgreSQL listo."

echo "Iniciando Odoo..."
docker run -d --name inmoser-odoo \
  --network "$NETWORK" \
  -p 127.0.0.1:$ODOO_PORT:8069 \
  -v odoo-data:/var/lib/odoo \
  -v "$ADDONS_HOST:/mnt/extra-addons:ro" \
  -e HOST=inmoser-db \
  -e USER="$ODOO_USER" \
  -e PASSWORD="$ODOO_PASS" \
  -e ODOO_ADMIN_PASSWORD="$ADMIN_PASS" \
  -e ADDONS_PATH=/mnt/extra-addons \
  "$ODOO_IMG"

INSTALL_LOG="$LOGDIR/install_${TIMESTAMP}.log"
TEST_LOG="$LOGDIR/test_${TIMESTAMP}.log"

echo "📦 Instalando módulo y ejecutando tests..."
docker exec -i inmoser-odoo odoo \
  -d "$ODOO_DB" \
  --stop-after-init \
  -i "$MODULO" \
  --test-enable \
  --addons-path=/mnt/extra-addons \
  2>&1 | tee "$INSTALL_LOG" "$TEST_LOG"

if grep -q "ERROR\|FAIL\|Traceback" "$TEST_LOG"; then
  echo "❌ Tests fallidos. Rollback completo..." | tee -a "$CHANGELOG"
  docker logs inmoser-odoo >> "$TEST_LOG"
  docker rm -f inmoser-odoo inmoser-db
  docker volume rm inmoser-db-data odoo-data 2>/dev/null || true
  exit 1
fi

echo "✅ Tests pasados. Verificando disponibilidad HTTP de Odoo..."

TRIES=0
MAX_TRIES=15
while true; do
  if curl -s "http://localhost:$ODOO_PORT" | grep -q "login"; then
    echo "Odoo está disponible en http://localhost:$ODOO_PORT"
    break
  fi
  ((TRIES++))
  if [[ $TRIES -gt $MAX_TRIES ]]; then
    echo "[ERROR] Odoo no responde en $ODOO_PORT"
    exit 1
  fi
  echo "Esperando Odoo... ($TRIES/$MAX_TRIES)"
  sleep 2
done

echo "📌 Despliegue exitoso – $TIMESTAMP" >> "$CHANGELOG"
