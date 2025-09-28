#!/bin/bash
echo "🔁 Reiniciando entorno Docker Odoo..."

# Ruta absoluta real del proyecto
PROJECT_ROOT="/home/baruc/odoo-inmoser_clean"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.yml"

# Validación semántica
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "❌ docker-compose.yml no encontrado en: $COMPOSE_FILE"
  exit 1
fi

# Ejecución
docker-compose -f "$COMPOSE_FILE" down -v
docker-compose -f "$COMPOSE_FILE" up --build -d

echo "✅ Odoo 17 lanzado en http://localhost:8069"
