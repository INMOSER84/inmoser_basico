#!/bin/bash

# Script para corregir automáticamente el módulo inmoser_service_order

# Configuración
REPO_URL="https://github.com/INMOSER84/inmoser_basico.git"
BRANCH_NAME="odoo17-auto-fixed"
MODULE_NAME="inmoser_service_order"
WORK_DIR="/tmp/odoo_fix_$$"

# Crear directorio de trabajo
mkdir -p $WORK_DIR
cd $WORK_DIR

# Clonar el repositorio
echo "Clonando repositorio..."
git clone $REPO_URL $MODULE_NAME
cd $MODULE_NAME

# Cambiar a la rama de adaptación
echo "Cambiando a la rama odoo17-adaptation..."
git checkout odoo17-adaptation

# Crear nueva rama para las correcciones automáticas
echo "Creando nueva rama $BRANCH_NAME..."
git checkout -b $BRANCH_NAME

# Función para crear archivos corregidos
create_fixed_files() {
    echo "Creando archivos corregidos..."
    
    # Corregir __manifest__.py
    cat > __manifest__.py << 'EOF'
{
    'name': 'Inmoser Service Order',
    'version': '17.0.1.0.0',
    'category': 'Service Management',
    'summary': 'Service Order Management for Inmoser',
    'author': 'INMOSER84',
    'website': 'https://github.com/INMOSER84/inmoser_service_order',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'mail', 'account', 'stock', 'hr', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/inmoser_security.xml',
        'data/service_type_data.xml',
        'data/ir_sequence_data.xml',
        'data/cron_jobs.xml',
        'data/email_templates.xml',
        'views/menu_items.xml',
        'views/service_order_views.xml',
        'views/service_order_actions.xml',
        'views/service_order_calendar.xml',
        'views/service_equipment_views.xml',
        'views/service_type_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/portal_templates.xml',
        'views/service_complete_wizard_views.xml',
        'views/service_reprogram_wizard_views.xml',
        'reports/service_order_report.xml',
        'reports/service_order_template.xml',
        'reports/service_certificate_template.xml',
        'reports/equipment_history_template.xml',
        'reports/technician_performance_template.xml',
        'static/src/xml/service_order_qr.xml',
        'static/src/xml/calendar_templates.xml',
    ],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {'python': ['qrcode']},
    'development_status': 'Beta',
    'price': 0,
    'currency': 'EUR',
}
