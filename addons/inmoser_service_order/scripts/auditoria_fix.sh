#!/bin/bash
MODULE_DIR=~/odoo-inmoser_clean/addons/inmoser_service_order
FIX_XML="$MODULE_DIR/fix_report_actions.xml"

echo "=== Generando XML de menús para actions de report sin menú ==="
echo "<odoo><data>" > $FIX_XML

grep -Hn '<record id="action_report_' $MODULE_DIR/reports/*.xml | while read -r line ; do
    FILE=$(echo $line | cut -d: -f1)
    ID=$(echo $line | grep -oP 'id="\Kaction_report_[^"]+')
    echo "Agregando menú para $ID desde $FILE"
    echo "  <menuitem id='menu_$ID' name='$ID' parent='menu_inmoser_reports' action='$ID'/>" >> $FIX_XML
done

echo "</data></odoo>" >> $FIX_XML
echo "✅ Archivo de fix generado en: $FIX_XML"
echo "Revisa y agrega este XML a tu módulo para que los reports tengan menú."
