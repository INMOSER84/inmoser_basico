from odoo.tests import TransactionCase, tagged
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestBusinessRules(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Crear un partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })
        
        # Crear un tipo de servicio
        self.service_type = self.env['service.type'].create({
            'name': 'Test Service Type',
            'duration': 2.0,
            'equipment_required': True,
            'technician_required': True,
        })
        
        # Crear un equipo
        self.equipment = self.env['service.equipment'].create({
            'name': 'Test Equipment',
            'serial_number': 'TEST001',
            'partner_id': self.partner.id,
        })
        
        # Crear un técnico
        self.technician = self.env['hr.employee'].create({
            'name': 'Test Technician',
            'is_technician': True,
        })
        
        # Crear una orden de servicio
        self.service_order = self.env['service.order'].create({
            'partner_id': self.partner.id,
            'service_type_id': self.service_type.id,
            'equipment_id': self.equipment.id,
            'technician_id': self.technician.id,
            'description': 'Test Service Order',
        })
    
    def test_validate_service_order(self):
        """Probar validación de orden de servicio"""
        business_logic = self.env['service.order.business.logic']
        
        # Orden de servicio válida
        errors = business_logic.validate_service_order(self.service_order)
        self.assertEqual(len(errors), 0)
        
        # Falta partner
        self.service_order.partner_id = False
        errors = business_logic.validate_service_order(self.service_order)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('Customer is required' in error for error in errors))
        
        # Restaurar partner
        self.service_order.partner_id = self.partner.id
        
        # Falta equipo (requerido para este tipo de servicio)
        self.service_order.equipment_id = False
        errors = business_logic.validate_service_order(self.service_order)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('Equipment is required' in error for error in errors))
    
    def test_calculate_service_duration(self):
        """Probar cálculo de duración de servicio"""
        business_logic = self.env['service.order.business.logic']
        
        # Duración base
        duration = business_logic.calculate_service_duration(self.service_order)
        self.assertEqual(duration, 2.0)
        
        # Agregar líneas de refacción
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'lst_price': 100.0,
        })
        
        self.env['service.order.refaction.line'].create({
            'order_id': self.service_order.id,
            'product_id': product.id,
            'quantity': 2.0,
            'unit_price': 100.0,
        })
        
        duration = business_logic.calculate_service_duration(self.service_order)
        self.assertEqual(duration, 3.0)  # 2.0 base + 0.5 por línea de refacción * 2 líneas
        
        # Cambiar prioridad
        self.service_order.priority = 'urgent'
        duration = business_logic.calculate_service_duration(self.service_order)
        self.assertEqual(duration, 4.5)  # 3.0 * 1.5 (factor urgente)
    
    def test_check_service_order_conflicts(self):
        """Probar detección de conflictos de orden de servicio"""
        business_logic = self.env['service.order.business.logic']
        
        # Programar la orden de servicio
        self.service_order.write({
            'date_scheduled': '2023-01-01 10:00:00',
            'state': 'scheduled',
        })
        
        # Crear otra orden de servicio para el mismo técnico al mismo tiempo
        conflicting_order = self.env['service.order'].create({
            'partner_id': self.partner.id,
            'service_type_id': self.service_type.id,
            'equipment_id': self.equipment.id,
            'technician_id': self.technician.id,
            'date_scheduled': '2023-01-01 11:00:00',
            'state': 'scheduled',
            'description': 'Conflicting Service Order',
        })
        
        # Verificar conflictos
        conflicts = business_logic.check_service_order_conflicts(conflicting_order)
        self.assertGreater(len(conflicts), 0)
        self.assertTrue(any('Overlapping' in conflict['reason'] for conflict in conflicts))
