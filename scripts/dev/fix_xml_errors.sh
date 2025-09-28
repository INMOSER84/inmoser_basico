#!/bin/bash

echo "🔧 Reparando errores XML comunes..."

FILES=(
  "$HOME/odoo-inmoser_clean/addons/inmoser_service_order/views/service_order_views.xml"
  "$HOME/odoo-inmoser_clean/addons/inmoser_service_order/reports/service_order_template.xml"
)

for FILE in "${FILES[@]}"; do
  echo "🧪 Analizando: $FILE"

  # Copia de seguridad
  cp "$FILE" "$FILE.bak"

  # Reparación básica: cerrar etiquetas huérfanas
  sed -i 's/<search[^>]*>/&\n<\/search>/g' "$FILE"
  sed -i 's/<t[^>]*>/&\n<\/t>/g' "$FILE"
  sed -i 's/<template[^>]*>/&\n<\/template>/g' "$FILE"
  sed -i 's/<data[^>]*>/&\n<\/data>/g' "$FILE"
  sed -i 's/<odoo[^>]*>/&\n<\/odoo>/g' "$FILE"

  # Validación post-reparación
  if xmllint --noout "$FILE"; then
    echo "✅ $FILE corregido y válido"
  else
    echo "❌ $FILE aún tiene errores. Revisa manualmente."
  fi
done

echo "🧾 Reparación completa. Se crearon backups .bak por seguridad."
