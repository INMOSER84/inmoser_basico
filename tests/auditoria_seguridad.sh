#!/usr/bin/env bash
set -euo pipefail

REPORT="/mnt/extra-addons/inmoser_service_order/.auditoria/informe_seguridad.txt"
ROOT_DIR="/mnt/extra-addons/inmoser_service_order"

echo "== Auditoría de Seguridad ==" | tee "$REPORT"

CSV="$ROOT_DIR/security/ir.model.access.csv"
if [ -f "$CSV" ]; then
  awk -F, 'NR>1{if($5=="1" && $3=="0"){print "Write sin Read en:",$2}}' "$CSV" | tee -a "$REPORT" || true
  awk -F, 'NR>1{print $2}' "$CSV" | sort -u | while read -r model; do
    if ! grep -Rq "_name[[:space:]]*=[[:space:]]*\"$model\"" "$ROOT_DIR/models"; then
      echo "Modelo ACL no encontrado: $model" | tee -a "$REPORT"
    fi
  done
fi

grep -RhoP 'groups="\K[^"]+' "$ROOT_DIR/views" "$ROOT_DIR/security" | tr ',' '\n' | sort -u | while read -r gid; do
  grep -Rq "id=\"$gid\"" "$ROOT_DIR/security" || echo "Grupo no definido: $gid" | tee -a "$REPORT"
done
