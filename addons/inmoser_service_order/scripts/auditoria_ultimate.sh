#!/bin/bash

MODULE_DIR=~/odoo-inmoser_clean/addons/inmoser_service_order
REPORT_FILE=~/odoo-inmoser_clean/addons/supreme17_ULTIMATE_report.html

echo "Generando auditoría del módulo $MODULE_DIR ..."

# Inicia HTML
cat <<HTML > $REPORT_FILE
<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Supreme17 ULTIMATE Report</title>
<style>
body{font-family:'Segoe UI', system-ui,sans-serif; background:#0d1117; color:#c9d1d9}
h1{background:linear-gradient(90deg,#0ff,#f0f); -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center; font-size:2.5rem;}
table{width:100%; border-collapse:collapse; margin-top:1rem;} th,td{padding:8px 12px; border:1px solid #30363d}
th{background:#161b22;} tr:nth-child(even){background:#161b22;} .ok{color:#0f0;} .ko{color:#f00;} .wa{color:#ff0;}
</style></head><body>
<h1>☆ Supreme17 ULTIMATE Report ☆</h1>
<p style="text-align:center">Generated: <span id="date"></span> – Module: <strong>inmoser_service_order</strong></p>
<script>document.getElementById('date').textContent=new Date().toLocaleString();</script>
<table><thead><tr><th>Tipo<th>Archivo<th>Detalle<th>Acción</tr></thead><tbody>
HTML

# 1. Templates de reportes
find $MODULE_DIR/reports/ -type f -name "*.xml" | while read f; do
    grep -Hn "<template" "$f" | while read l; do
        echo "<tr class=ok><td>XML<td>$f<td>$l<td class=ok>OK</td></tr>" >> $REPORT_FILE
    done
done

# 2. IDs duplicados
find $MODULE_DIR/reports/ -type f -name "*.xml" -exec grep -oP 'id="\K[^"]+' {} \; | sort | uniq -c | sort -nr | awk '$1>1{print "DUPLICADO: "$0}' | while read d; do
    echo "<tr class=ko><td>XML<td>Reporte<td>$d<td class=wa>Revisar</td></tr>" >> $REPORT_FILE
done

# 3. Revisar actions sin menú
grep -rhoP '<record[^>]*model="ir.actions.report"[^>]*id="\K[^"]+' $MODULE_DIR/reports/*.xml | while read act; do
    menu=$(grep -r "$act" $MODULE_DIR/views/*.xml)
    if [ -z "$menu" ]; then
        echo "<tr class=wa><td>XML<td>Action without menu<td>$act<td class=wa>Revisar</td></tr>" >> $REPORT_FILE
    fi
done

# 4. QWeb templates duplicados
find $MODULE_DIR/static/src/xml/ -type f -name "*.xml" -exec grep -oP 't-name="\K[^"]+' {} \; | sort | uniq -c | sort -nr | awk '$1>1{print "DUPLICADO: "$0}' | while read q; do
    echo "<tr class=ko><td>QWeb<td>Static XML<td>$q<td class=wa>Revisar</td></tr>" >> $REPORT_FILE
done

# Finaliza HTML
cat <<HTML >> $REPORT_FILE
</tbody></table></body></html>
HTML

echo "✅ Auditoría generada en $REPORT_FILE"
