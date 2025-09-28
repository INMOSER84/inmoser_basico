#!/usr/bin/env bash
set -euo pipefail

MOD_NAME="inmoser_service_order"
ROOT_DIR="/mnt/extra-addons/$MOD_NAME"
TS="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="$ROOT_DIR/.auditoria"
REPORT="$LOG_DIR/informe_preinstalacion_${TS}.txt"
DB_TMP="audit_${MOD_NAME}_${TS}"

mkdir -p "$LOG_DIR"
echo "[BEGIN] Auditoría $MOD_NAME @ $TS" | tee "$REPORT"

# 1. Entorno
echo "== Entorno ==" | tee -a "$REPORT"
python3 -c "import sys; print(sys.version)" | tee -a "$REPORT"
psql --version | tee -a "$REPORT"

# 2. Checksums
echo "== Checksums ==" | tee -a "$REPORT"
find "$ROOT_DIR" -type f -not -path "*/__pycache__/*" -print0 | xargs -0 sha256sum > "$LOG_DIR/checksum_${TS}.sha256"
wc -l "$LOG_DIR/checksum_${TS}.sha256" | tee -a "$REPORT"

# 3. Manifest
echo "== Manifest ==" | tee -a "$REPORT"
python3 - <<'PY' | tee -a "$REPORT"
import ast, os
root = "/mnt/extra-addons/inmoser_service_order"
mf = os.path.join(root, "__manifest__.py")
with open(mf, 'r', encoding='utf-8') as f:
    data = ast.literal_eval(f.read())
keys_required = ["name","version","depends","data","license","installable"]
missing = [k for k in keys_required if k not in data]
print("Faltan claves:", missing)
print("Data:", data.get("data", []))
print("Demo:", data.get("demo", []))
print("Depends:", data.get("depends", []))
PY

# 4. XML lint
echo "== XML ==" | tee -a "$REPORT"
find "$ROOT_DIR" -name "*.xml" -exec xmllint --noout {} \; 2>>"$REPORT" || true

# 5. Seguridad
echo "== Seguridad ==" | tee -a "$REPORT"
CSV="$ROOT_DIR/security/ir.model.access.csv"
if [ -f "$CSV" ]; then
  awk -F, 'NR>1{if($5=="1" && $3=="0"){print "Write sin Read en:",$2}}' "$CSV" | tee -a "$REPORT" || true
fi

# 6. Dry-run instalación
echo "== Dry-run ==" | tee -a "$REPORT"
createdb "$DB_TMP"
odoo -d "$DB_TMP" --stop-after-init -i "$MOD_NAME" --addons-path="/mnt/extra-addons" | tee -a "$REPORT" || echo "Dry-run reportó errores" | tee -a "$REPORT"
dropdb "$DB_TMP"

echo "[END] Auditoría $MOD_NAME @ $TS" | tee -a "$REPORT"
