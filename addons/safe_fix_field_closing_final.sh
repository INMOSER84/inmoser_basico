#!/bin/bash
# safe_fix_field_closing_final.sh
# Convierte <field ... /> a <field ...></field> en todos los XML del módulo

MODULE=${1:-inmoser_service_order}
BASE_DIR="$HOME/odoo-inmoser_clean/addons"
MODULE_DIR="$BASE_DIR/$MODULE"

find "$MODULE_DIR" -type f -iname "*.xml" | while read -r FILE; do
  echo "📄 Procesando $FILE"
  cp "$FILE" "${FILE}.bak"
  sed -i 's|<field \([^>]*\)/>|<field \1></field>|g' "$FILE"
done

echo "✅ Todos los <field ... /> convertidos a <field ...></field>"
