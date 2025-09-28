k```bash
#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(pwd)"
MODEL="models/service_equipment.py"
VIEW="views/service_equipment_views.xml"

if [ ! -f "$MODEL" ]; then
  echo "ERROR: modelo no encontrado: $MODEL"
  exit 1
fi
if [ ! -f "$VIEW" ]; then
  echo "ERROR: vista no encontrada: $VIEW"
  exit 1
fi

BACKUP="${VIEW}.bak.$(date +%s)"
cp -v "$VIEW" "$BACKUP"

TMP_DEF="/tmp/defined_fields.$$"
TMP_XML="/tmp/xml_fields.$$"
TMP_NOT="/tmp/not_defined_fields.$$"

# Extraer campos definidos en el modelo (lado izquierdo de "=" cuando es fields.*)
awk -F= '/= *fields\./{
  name=$1
  gsub(/^[ \t]+|[ \t]+$/, "", name)
  print name
}' "$MODEL" | sort -u > "$TMP_DEF"

# Extraer nombres de campos en la vista (atributo name="...")
grep -oP '<field[^>]*name="[^"]+"' "$VIEW" \
  | sed -E 's/.*name="([^"]+)".*/\1/' \
  | sort -u > "$TMP_XML"

# Campos en vista pero no en modelo
comm -23 "$TMP_XML" "$TMP_DEF" > "$TMP_NOT" || true

if [ ! -s "$TMP_NOT" ]; then
  echo "[OK] No hay campos indefinidos en la vista."
  exit 0
fi

echo "Campos detectados en la vista que NO están definidos en el modelo ($MODEL):"
cat "$TMP_NOT"

# Eliminar <field name="X"/> de la vista
while read -r field; do
  if [ -n "$field" ]; then
    echo " - Eliminando <$field> de $VIEW"
    sed -i "/<field[^>]*name=\"$field\"/d" "$VIEW"
  fi
done < "$TMP_NOT"

echo "[DONE] Vista corregida. Respaldo en: $BACKUP"
```

