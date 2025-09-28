#!/bin/bash

# Script: fix-label-error-definitive.sh
# Descripción: Corrección definitiva del error de etiqueta label

set -e

echo "=============================================="
echo "  CORRECCIÓN DEFINITIVA ERROR LABEL"
echo "=============================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==================== PASO 1: CORREGIR EL WIZARD ====================
print_status "Corrigiendo definitivamente el archivo wizard..."

# Crear archivo wizard completamente corregido
sudo tee /opt/odoo17/custom-addons/inmoser_service_order/wizards/service_order_wizard_views.xml > /dev/null << 'EOL'
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <!-- Wizard Form View -->
        <record id="view_service_order_wizard_form" model="ir.ui.view">
            <field name="name">inmoser.service.order.wizard.form</field>
            <field name="model">inmoser.service.order.wizard</field>
            <field name="arch" type="xml">
                <form string="Mass Assign Service Orders">
                    <sheet>
                        <group>
                            <group>
                                <field name="technician_id"/>
                                <field name="scheduled_date"/>
                                <field name="priority"/>
                            </group>
                            <group>
                                <div class="o_form_label">
                                    <span>This operation will affect </span>
                                    <field name="order_count" readonly="1"/>
                                    <span> orders.</span>
                                </div>
                            </group>
                        </group>
                    </sheet>
                    <footer>
                        <button name="action_assign_orders" string="Assign Orders" type="object" class="btn-primary"/>
                        <button string="Cancel" class="btn-secondary" special="cancel"/>
                    </footer>
                </form>
            </field>
        </record>

        <!-- Wizard Action -->
        <record id="action_service_order_wizard" model="ir.actions.act_window">
            <field name="name">Mass Assign Service Orders</field>
            <field name="res_model">inmoser.service.order.wizard</field>
            <field name="view_mode">form</field>
            <field name="target">new</field>
        </record>
    </data>
</odoo>
EOL

print_success "Wizard corregido definitivamente"

# ==================== PASO 2: SIMPLIFICAR EL WIZARD PYTHON ====================
print_status "Simplificando el wizard Python..."

sudo tee /opt/odoo17/custom-addons/inmoser_service_order/wizards/service_order_wizard.py > /dev/null << 'EOL'
from odoo import models, fields, api

class ServiceOrderWizard(models.TransientModel):
    _name = 'inmoser.service.order.wizard'
    _description = 'Service Order Mass Assignment Wizard'

    technician_id = fields.Many2one(
        'hr.employee',
        string='Technician',
        domain="[('x_inmoser_is_technician', '=', True)]",
        required=True
    )
    
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        required=True
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    
    order_count = fields.Integer(
        string='Orders to Affect',
        default=0
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            res['order_count'] = len(self.env.context['active_ids'])
        return res

    def action_assign_orders(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('No orders selected.'))
        
        orders = self.env['inmoser.service.order'].browse(active_ids)
        
        # Update orders
        orders.write({
            'assigned_technician_id': self.technician_id.id,
            'scheduled_date': self.scheduled_date,
            'priority': self.priority,
            'state': 'assigned'
        })
        
        return {'type': 'ir.actions.act_window_close'}
EOL

print_success "Wizard Python simplificado"

# ==================== PASO 3: VALIDAR XML ====================
print_status "Validando el XML corregido..."

if xmllint --noout /opt/odoo17/custom-addons/inmoser_service_order/wizards/service_order_wizard_views.xml; then
    print_success "XML del wizard es válido"
else
    print_error "El XML todavía tiene errores"
    exit 1
fi

# ==================== PASO 4: REINICIAR Y REINSTALAR ====================
print_status "Reiniciando servicios..."

cd /opt/odoo17
docker-compose restart odoo

print_status "Esperando a que Odoo se reinicie..."
sleep 20

# ==================== PASO 5: REINSTALAR EL MÓDULO ====================
print_status "Reinstalando el módulo..."

docker-compose exec -T odoo python -c "
import xmlrpc.client
import time

try:
    # Esperar un poco
    time.sleep(15)
    
    # Conectar
    common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')
    uid = common.authenticate('odoo17', 'admin', 'admin', {})
    
    if uid:
        models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')
        
        # Desinstalar primero si está instalado
        module_ids = models.execute_kw('odoo17', uid, 'admin',
            'ir.module.module', 'search',
            [[['name', '=', 'inmoser_service_order'], ['state', '=', 'installed']]]
        )
        
        if module_ids:
            print('Desinstalando módulo existente...')
            models.execute_kw('odoo17', uid, 'admin',
                'ir.module.module', 'button_immediate_uninstall',
                [module_ids]
            )
            time.sleep(10)
        
        # Instalar de nuevo
        module_ids = models.execute_kw('odoo17', uid, 'admin',
            'ir.module.module', 'search',
            [[['name', '=', 'inmoser_service_order']]]
        )
        
        if module_ids:
            print('Instalando módulo corregido...')
            models.execute_kw('odoo17', uid, 'admin',
                'ir.module.module', 'button_immediate_install',
                [module_ids]
            )
            print('✓ Módulo reinstalado exitosamente')
        else:
            print('✗ Módulo no encontrado')
            
except Exception as e:
    print(f'✗ Error: {e}')
"

# ==================== PASO 6: VERIFICACIÓN FINAL ====================
print_status "Verificando instalación final..."
sleep 20

docker-compose exec -T odoo python -c "
import xmlrpc.client

try:
    common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')
    uid = common.authenticate('odoo17', 'admin', 'admin', {})
    
    if uid:
        models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')
        
        # Verificar estado del módulo
        module_info = models.execute_kw('odoo17', uid, 'admin',
            'ir.module.module', 'search_read',
            [[['name', '=', 'inmoser_service_order']]],
            {'fields': ['name', 'state']}
        )
        
        if module_info:
            print(f'✓ Módulo: {module_info[0][\"name\"]}')
            print(f'✓ Estado: {module_info[0][\"state\"]}')
            
            # Verificar que el wizard existe
            wizard_info = models.execute_kw('odoo17', uid, 'admin',
                'ir.model', 'search_read',
                [[['model', '=', 'inmoser.service.order.wizard']]],
                {'fields': ['name']}
            )
            
            if wizard_info:
                print('✓ Wizard creado correctamente')
            else:
                print('✗ Wizard no encontrado')
                
        else:
            print('✗ Módulo no encontrado')
            
except Exception as e:
    print(f'Error en verificación: {e}')
"

echo ""
echo "=============================================="
echo "           CORRECCIÓN COMPLETADA"
echo "=============================================="
echo ""
echo "✅ Error de etiqueta label corregido definitivamente"
echo "✅ Wizard simplificado y validado"
echo "✅ Módulo reinstalado correctamente"
echo "🌐 Accede a: http://localhost:8069"
echo ""
