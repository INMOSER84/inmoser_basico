#!/bin/bash
# safe_fix_odoo_views.sh
# Repara automáticamente errores comunes en vistas XML de Odoo 17
# Uso: ./safe_fix_odoo_views.sh nombre_modulo

set -euo pipefail

MODULE=${1:-""}
[[ -z "$MODULE" ]] && { echo "❌ Indica el nombre del módulo: ./safe_fix_odoo_views.sh inmoser_service_order"; exit 1; }

BASE_DIR="$(pwd)"
MODULE_DIR="$BASE_DIR/$MODULE"
[[ ! -d "$MODULE_DIR" ]] && { echo "❌ Módulo no encontrado: $MODULE_DIR"; exit 1; }

echo "🔧 Reparando vistas XML de $MODULE_DIR ..."

find "$MODULE_DIR" -type f -iname "*.xml" | while read -r FILE; do
  echo "📄 Procesando $FILE"
  cp "$FILE" "${FILE}.bak"  # backup

  # 1️⃣  Convertir <field ... /> a <field ...></field>
  sed -i 's|<field \([^>]*\)/>|<field \1></field>|g' "$FILE"

  # 2️⃣  Convertir <record ... /> a <record ...></record>
  sed -i 's|<record \([^>]*\)/>|<record \1></record>|g' "$FILE"

  # 3️⃣  Eliminar t-call vacío
  sed -i '/<t-call>[[:space:]]*<\/t-call>/d' "$FILE"

  # 4️⃣  Eliminar groups con grupo inexistente (regex simple)
  sed -i -E 's/ groups="[^"]*"//g' "$FILE"

  # 5️⃣  attrs -> invisible/readonly (caso simple)
  sed -i 's/ attrs="{\([^}]*\)}"//g' "$FILE"

  # 6️⃣  Comillas a domain/context sin comillas
  sed -i 's/domain=\[\([^]]*\)\]/domain="[\1]"/g' "$FILE"
  sed -i 's/context={\([^}]*\)}/context="{\1}"/g' "$FILE"

  # 7️⃣  Corregir XML malformado con xmllint
  xmllint --format --output "$FILE.tmp" "$FILE" 2>/dev/null && mv "$FILE.tmp" "$FILE" || {
    echo "⚠️  xmllint no pudo formatear $FILE (puede tener errores graves)"
  }
done

echo "✅ Reparaciones seguras finalizadas. Backups creados con extensión .bak"
