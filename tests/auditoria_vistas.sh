#!/usr/bin/env bash
set -euo pipefail

REPORT="/mnt/extra-addons/inmoser_service_order/.auditoria/informe_vistas.txt"
ROOT_DIR="/mnt/extra-addons/inmoser_service_order"

echo "== Auditoría de Vistas ==" | tee "$REPORT"

# IDs duplicados
grep -RhoP 'id="\K[^"]+' "$ROOT_DIR/views" | sort | uniq -d | tee -a "$REPORT" || echo "Sin ids duplicados" | tee -a "$REPORT"

# Botones sin método
grep -RhoP '<button[^>]+name="\K[^"]+' "$ROOT_DIR/views" | sort -u > /tmp/buttons.txt
while read -r m; do
  if ! grep -Rq "def[[:space:]]+$m\\b" "$ROOT_DIR/models" "$ROOT_DIR/wizards"; then
    echo "FALTA método: $m" | tee -a "$REPORT"
  fi
done < /tmp/buttons.txt

# Campos inexistentes
grep -RhoP '<field[^>]+name="\K[^"]+' "$ROOT_DIR/views" | sort -u > /tmp/fields.txt
while read -r f; do
  if ! grep -Rq "$f" "$ROOT_DIR/models"; then
    echo "Verificar campo: $f" | tee -a "$REPORT"
  fi
done < /tmp/fields.txt

# Atributos obsoletos
grep -RnoE "attrs=.*state|states=" "$ROOT_DIR/views" || echo "Sin patrones críticos detectados" | tee -a "$REPORT"
