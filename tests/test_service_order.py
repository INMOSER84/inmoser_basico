from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestServiceOrder(TransactionCase):
    
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
            'equipment_required': False,
            'technician_required': True,
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
            'technician_id': self.technician.id,
            'description': 'Test Service Order',
        })
    
    def test_service_order_creation(self):
        """Probar creación de orden de servicio"""
        self.assertEqual(self.service_order.state, 'draft')
        self.assertTrue(self.service_order.name.startswith('SO/'))
    
    def test_service_order_schedule(self):
        """Probar programación de orden de servicio"""
        self.service_order.action_schedule()
        self.assertEqual(self.service_order.state, 'scheduled')
    
    def test_service_order_start(self):
        """Probar inicio de orden de servicio"""
        self.service_order.action_schedule()
        self.service_order.action_start()
        self.assertEqual(self.service_order.state, 'in_progress')
        self.assertTrue(self.service_order.date_started)
    
    def test_service_order_complete(self):
        """Probar completado de orden de servicio"""
        self.service_order.action_schedule()
        self.service_order.action_start()
        
        # Completar la orden de servicio
        wizard = self.env['service.complete.wizard'].with_context(active_id=self.service_order.id).create({
            'completion_date': '2023-01-01 12:00:00',
            'notes': 'Test completion notes',
        })
        wizard.action_complete()
        
        self.assertEqual(self.service_order.state, 'completed')
        self.assertTrue(self.service_order.date_completed)
    
    def test_service_order_cancel(self):
        """Probar cancelación de orden de servicio"""
        self.service_order.action_cancel()
        self.assertEqual(self.service_order.state, 'cancelled')
    
    def test_service_order_refaction_line(self):
        """Probar línea de refacción de orden de servicio"""
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'lst_price': 100.0,
        })
        
        refaction_line = self.env['service.order.refaction.line'].create({
            'order_id': self.service_order.id,
            'product_id': product.id,
            'quantity': 2.0,
            'unit_price': 100.0,
        })
        
        self.assertEqual(refaction_line.subtotal, 200.0)
        self.assertEqual(len(self.service_order.refaction_line_ids), 1)
