#!/bin/bash
echo "==== AUDITORIA ODOO 17 COMMUNITY ===="
echo
echo "1. Constructos PYTHON obsoletos"
obsoletos=("digits=(" "track_visibility" "oldname=" "_flush_search")
for obs in "${obsoletos[@]}"; do
  echo "  Buscando: $obs"
  grep -Rn "$obs" --include="*.py" . || echo "    ✔ No encontrado"
done

echo
echo "2. Constructos XML obsoletos"
obsxml=("colors=" "t-esc" "t-raw" "<report" "kanban-box")
for obs in "${obsxml[@]}"; do
  echo "  Buscando: $obs"
  grep -Rn "$obs" --include="*.xml" . || echo "    ✔ No encontrado"
done

echo
echo "3. Importaciones JS obsoletas"
grep -Rn "jsonrpc" --include="*.js" . || echo "  ✔ No encontrado"

echo
echo "4. Claves faltantes en __manifest__.py"
grep -q "license" __manifest__.py || echo "  ⚠ Añade 'license': 'LGPL-3'"
grep -q "version" __manifest__.py || echo "  ⚠ Añade 'version': '17.0.1.0.0'"

echo
echo "5. Versión debe empezar por 17.0"
grep "version" __manifest__.py | grep -q "17\.0\." && echo "  ✔ Correcta" || echo "  ⚠ Debe empezar por 17.0.x"

echo
echo "==== FIN AUDITORIA ===="
