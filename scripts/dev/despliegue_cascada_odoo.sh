#!/bin/bash
# Despliegue modular en cascada – Inmoser DevOps

set -euo pipefail

# Configuración general
ODOO_DB="${ODOO_DB:-inmoser17}"
ODOO_PORT="${ODOO_PORT:-8069}"
ADDONS_HOST="$HOME/odoo-inmoser_clean/addons"
MODULOS=("inmoser_service_order" "inmoser_equipment" "inmoser_portal")  # ← ajusta según tus módulos
LOGDIR="$HOME/odoo-inmoser_clean/logs"
CHANGELOG="$LOGDIR/changelog.txt"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$LOGDIR"

# Validar y desplegar cada módulo
for MODULO in "${MODULOS[@]}"; do
  MODULO_PATH="$ADDONS_HOST/$MODULO"
  echo "🔍 Validando módulo: $MODULO"

  if ! "$HOME/odoo-inmoser_clean/scripts/dev/simular_instalacion_odoo.sh" "$MODULO_PATH"; then
    echo "❌ Error en $MODULO. Abortando cascada." | tee -a "$CHANGELOG"
    exit 1
  fi

  echo "📦 Instalando módulo: $MODULO"
  INSTALL_LOG="$LOGDIR/install_${MODULO}_${TIMESTAMP}.log"
  TEST_LOG="$LOGDIR/test_${MODULO}_${TIMESTAMP}.log"

  docker exec -i inmoser-odoo odoo \
    -d "$ODOO_DB" \
    --stop-after-init \
    -i "$MODULO" \
    --test-enable \
    --addons-path=/mnt/extra-addons \
    2>&1 | tee "$INSTALL_LOG" "$TEST_LOG"

  if grep -q "ERROR\|FAIL\|Traceback" "$TEST_LOG"; then
    echo "❌ Tests fallidos en $MODULO. Rollback completo..." | tee -a "$CHANGELOG"
    docker logs inmoser-odoo >> "$TEST_LOG"
    docker rm -f inmoser-odoo inmoser-db
    docker volume rm inmoser-db-data odoo-data 2>/dev/null || true
    exit 1
  fi

  echo "✅ $MODULO instalado y validado correctamente" | tee -a "$CHANGELOG"
done

echo "🎉 Todos los módulos fueron instalados y validados correctamente"
echo "📌 Despliegue en cascada exitoso – $TIMESTAMP" >> "$CHANGELOG"
