#!/bin/bash
# Auditoría avanzada de inmoser_service_order para Odoo 17 (solo terminal)

MODULE_DIR=~/odoo-inmoser_clean/addons/inmoser_service_order

# Colores para terminal
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # Sin color

echo -e "${GREEN}=== AUDITORÍA TERMINAL 100%: inmoser_service_order ===${NC}"

# 1. Templates de reportes
echo -e "\n${GREEN}1. Templates de reportes:${NC}"
REPORT_TEMPLATES=$(find $MODULE_DIR/reports/ -type f -name "*.xml" -exec grep -Hn "<template" {} \;)
echo "$REPORT_TEMPLATES"

# 2. IDs duplicados en reportes
echo -e "\n${YELLOW}2. IDs duplicados en reportes:${NC}"
DUP_IDS=$(find $MODULE_DIR/reports/ -type f -name "*.xml" -exec grep -oP 'id="\K[^"]+' {} \; | sort | uniq -c | awk '$1>1')
if [[ -z "$DUP_IDS" ]]; then
    echo -e "${GREEN}No hay IDs duplicados en reportes.${NC}"
else
    echo -e "${RED}$DUP_IDS${NC}"
fi

# 3. Actions de report sin menú
echo -e "\n${YELLOW}3. Actions de report sin menú asociado:${NC}"
ACTIONS_NO_MENU=$(grep -r "ir.actions.report" $MODULE_DIR/reports/*.xml | grep -v "menu")
if [[ -z "$ACTIONS_NO_MENU" ]]; then
    echo -e "${GREEN}Todos los reports tienen un menú asociado o se detecta correcto.${NC}"
else
    echo -e "${RED}$ACTIONS_NO_MENU${NC}"
fi

# 4. Templates QWeb
echo -e "\n${GREEN}4. QWeb templates:${NC}"
QWEB_TEMPLATES=$(find $MODULE_DIR/static/src/xml/ -type f -name "*.xml" -exec grep -Hn "<t t-name=" {} \;)
echo "$QWEB_TEMPLATES"

# 5. IDs duplicados QWeb
echo -e "\n${YELLOW}5. QWeb templates duplicados:${NC}"
DUP_QWEB=$(find $MODULE_DIR/static/src/xml/ -type f -name "*.xml" -exec grep -oP 't-name="\K[^"]+' {} \; | sort | uniq -c | awk '$1>1')
if [[ -z "$DUP_QWEB" ]]; then
    echo -e "${GREEN}No hay QWeb duplicados.${NC}"
else
    echo -e "${RED}$DUP_QWEB${NC}"
fi

# 6. Validar templates referenciados
echo -e "\n${YELLOW}6. Templates referenciados que no existen:${NC}"
MISSING_CALLS=""
for call in $(grep -rhoP 't-call="\K[^"]+' $MODULE_DIR/reports/*.xml $MODULE_DIR/static/src/xml/*.xml | sort | uniq); do
    grep -Rq "$call" $MODULE_DIR/reports/*.xml $MODULE_DIR/static/src/xml/*.xml > /dev/null
    if [ $? -ne 0 ]; then
        MISSING_CALLS+="$call\n"
    fi
done
if [[ -z "$MISSING_CALLS" ]]; then
    echo -e "${GREEN}Todos los templates referenciados existen.${NC}"
else
    echo -e "${RED}$MISSING_CALLS${NC}"
fi

# 7. Resumen final
echo -e "\n${GREEN}=== RESUMEN FINAL ===${NC}"
echo -e "Templates de reportes: $(echo "$REPORT_TEMPLATES" | wc -l)"
echo -e "IDs duplicados en reportes: $(echo "$DUP_IDS" | wc -l)"
echo -e "Actions sin menú: $(echo "$ACTIONS_NO_MENU" | wc -l)"
echo -e "QWeb templates: $(echo "$QWEB_TEMPLATES" | wc -l)"
echo -e "QWeb duplicados: $(echo "$DUP_QWEB" | wc -l)"
echo -e "Templates referenciados faltantes: $(echo -e "$MISSING_CALLS" | wc -l)"
