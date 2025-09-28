#!/usr/bin/env bash
set -euo pipefail

REPORT="/mnt/extra-addons/inmoser_service_order/.auditoria/informe_manifest.txt"

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
