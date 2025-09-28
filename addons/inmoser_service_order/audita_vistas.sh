#!/bin/bash
# audita_vistas.sh
# Auditoría completa de vistas XML para Odoo 17

MODULO_DIR=$(pwd)
LOG_FILE="$MODULO_DIR/fix_relaxng_report.log"

echo "🔍 Iniciando auditoría de vistas XML en $MODULO_DIR"
echo "Fecha: $(date)" > "$LOG_FILE"

# Buscar todos los XML en el módulo
find $MODULO_DIR/views $MODULO_DIR/data $MODULO_DIR/demo $MODULO_DIR/reports -name "*.xml" | while read xmlfile; do
    echo "Analizando $xmlfile ..." | tee -a "$LOG_FILE"
    xmllint --noout --schema /usr/share/odoo/17.0/server/odoo/addons/base/data/ir_ui_view.xsd "$xmlfile" 2>>"$LOG_FILE"
    if [ $? -eq 0 ]; then
        echo "✅ OK: $xmlfile" | tee -a "$LOG_FILE"
    else
        echo "❌ ERROR en $xmlfile" | tee -a "$LOG_FILE"
    fi
done

echo "Auditoría completada. Revisa $LOG_FILE para detalles."
