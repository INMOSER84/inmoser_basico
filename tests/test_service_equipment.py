from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestServiceEquipment(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Crear un partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })
        
        # Crear un equipo
        self.equipment = self.env['service.equipment'].create({
            'name': 'Test Equipment',
            'serial_number': 'TEST001',
            'model': 'Test Model',
            'manufacturer': 'Test Manufacturer',
            'partner_id': self.partner.id,
            'location': 'Test Location',
            'service_interval': 365,
        })
    
    def test_equipment_creation(self):
        """Probar creación de equipo"""
        self.assertTrue(self.equipment.name)
        self.assertTrue(self.equipment.next_service_date)
    
    def test_equipment_qr_code(self):
        """Probar generación de código QR del equipo"""
        self.assertTrue(self.equipment.qr_code)
    
    def test_equipment_service_history(self):
        """Probar historial de servicio del equipo"""
        # Crear una orden de servicio para el equipo
        service_type = self.env['service.type'].create({
            'name': 'Test Service Type',
            'duration': 2.0,
            'equipment_required': True,
            'technician_required': True,
        })
        
        technician = self.env['hr.employee'].create({
            'name': 'Test Technician',
            'is_technician': True,
        })
        
        service_order = self.env['service.order'].create({
            'partner_id': self.partner.id,
            'service_type_id': service_type.id,
            'equipment_id': self.equipment.id,
            'technician_id': technician.id,
            'description': 'Test Service Order',
        })
        
        self.assertEqual(len(self.equipment.service_order_ids), 1)
        self.assertEqual(self.equipment.service_order_ids[0], service_order)
