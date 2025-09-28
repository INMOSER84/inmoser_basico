#!/bin/bash
# safe_fix_odoo_views_v3.sh
# Repara XML malformado y field vacíos en Odoo 17
# Uso: ./safe_fix_odoo_views_v3.sh inmoser_service_order

set -euo pipefail

MODULE=${1:-""}
[[ -z "$MODULE" ]] && { echo "❌ Indica el módulo: ./safe_fix_odoo_views_v3.sh inmoser_service_order"; exit 1; }

BASE_DIR="$(pwd)"
MODULE_DIR="$BASE_DIR/$MODULE"
[[ ! -d "$MODULE_DIR" ]] && { echo "❌ Módulo no encontrado: $MODULE_DIR"; exit 1; }

echo "🔧 Reparando XML malformado en $MODULE_DIR ..."

find "$MODULE_DIR" -type f -iname "*.xml" | while read -r FILE; do
  echo "📄 Procesando $FILE"
  cp "$FILE" "${FILE}.bak"

  # 1️⃣  Eliminar contenido después de </odoo>
  sed -i '/^<\/odoo>/q' "$FILE"

  # 2️⃣  Cerrar <data> si está abierto
  if grep -q '<data>' "$FILE" && ! grep -q '</data>' "$FILE"; then
    echo '</data>' >> "$FILE"
  fi

  # 3️⃣  Cerrar <odoo> si está abierto
  if grep -q '<odoo>' "$FILE" && ! grep -q '</odoo>' "$FILE"; then
    echo '</odoo>' >> "$FILE"
  fi

  # 4️⃣  Convertir <field ... /> a <field ...></field>
  sed -i 's|<field \([^>]*\)/>|<field \1></field>|g' "$FILE"

  # 5️⃣  Convertir <record ... /> a <record ...></record>
  sed -i 's|<record \([^>]*\)/>|<record \1></record>|g' "$FILE"

  # 6️⃣  Intentar formatear con xmllint (si se puede)
  xmllint --format --output "$FILE.tmp" "$FILE" 2>/dev/null && mv "$FILE.tmp" "$FILE" || {
    echo "⚠️  xmllint no pudo formatear $FILE (puede tener errores graves)"
  }
done

echo "✅ Reparaciones finalizadas. Backups en .bak"
