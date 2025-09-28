from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestServiceWorkflows(TransactionCase):
    
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
    
    def test_complete_workflow(self):
        """Probar flujo de trabajo completo de orden de servicio"""
        # Estado inicial
        self.assertEqual(self.service_order.state, 'draft')
        
        # Programar
        self.service_order.action_schedule()
        self.assertEqual(self.service_order.state, 'scheduled')
        self.assertTrue(self.service_order.date_scheduled)
        
        # Iniciar
        self.service_order.action_start()
        self.assertEqual(self.service_order.state, 'in_progress')
        self.assertTrue(self.service_order.date_started)
        
        # Completar
        wizard = self.env['service.complete.wizard'].with_context(active_id=self.service_order.id).create({
            'completion_date': '2023-01-01 12:00:00',
            'notes': 'Test completion notes',
        })
        wizard.action_complete()
        
        self.assertEqual(self.service_order.state, 'completed')
        self.assertTrue(self.service_order.date_completed)
    
    def test_reprogram_workflow(self):
        """Probar flujo de trabajo de reprogramación de orden de servicio"""
        # Programar la orden de servicio
        self.service_order.action_schedule()
        self.assertEqual(self.service_order.state, 'scheduled')
        original_date = self.service_order.date_scheduled
        
        # Reprogramar
        wizard = self.env['service.reprogram.wizard'].with_context(active_id=self.service_order.id).create({
            'new_date': '2023-01-02 10:00:00',
            'reason': 'Test reprogramming reason',
        })
        wizard.action_reprogram()
        
        self.assertEqual(self.service_order.state, 'scheduled')
        self.assertNotEqual(self.service_order.date_scheduled, original_date)
        self.assertEqual(self.service_order.date_scheduled, '2023-01-02 10:00:00')
    
    def test_cancel_workflow(self):
        """Probar flujo de trabajo de cancelación de orden de servicio"""
        # Programar la orden de servicio
        self.service_order.action_schedule()
        self.assertEqual(self.service_order.state, 'scheduled')
        
        # Cancelar
        self.service_order.action_cancel()
        self.assertEqual(self.service_order.state, 'cancelled')
        
        # No se puede cancelar nuevamente
        with self.assertRaises(Exception):
            self.service_order.action_cancel()
