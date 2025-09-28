from odoo.tests import TransactionCase, tagged
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestIntegrations(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Crear un partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })
        
        # Crear un tipo de servicio con un producto
        self.product = self.env['product.product'].create({
            'name': 'Test Service Product',
            'lst_price': 100.0,
            'type': 'service',
        })
        
        self.service_type = self.env['service.type'].create({
            'name': 'Test Service Type',
            'duration': 2.0,
            'equipment_required': False,
            'technician_required': True,
            'product_id': self.product.id,
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
    
    def test_account_integration(self):
        """Probar integración contable"""
        # Agregar una línea de refacción
        refaction_product = self.env['product.product'].create({
            'name': 'Test Refaction Product',
            'lst_price': 50.0,
        })
        
        self.env['service.order.refaction.line'].create({
            'order_id': self.service_order.id,
            'product_id': refaction_product.id,
            'quantity': 2.0,
            'unit_price': 50.0,
        })
        
        # Crear factura
        account_integration = self.env['account.integration']
        invoice = account_integration.create_invoice_from_service_order(self.service_order)
        
        self.assertTrue(invoice)
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(len(invoice.invoice_line_ids), 2)  # Tipo de servicio + línea de refacción
        self.assertTrue(self.service_order.is_invoiced)
    
    def test_hr_integration(self):
        """Probar integración de RRHH"""
        hr_integration = self.env['hr.integration']
        
        # Programar orden de servicio
        success = hr_integration.schedule_service_order(self.service_order)
        self.assertTrue(success)
        self.assertEqual(self.service_order.state, 'scheduled')
        self.assertTrue(self.service_order.date_scheduled)
        
        # Verificar disponibilidad del técnico
        available = hr_integration.check_technician_availability(
            self.technician,
            self.service_order.date_scheduled,
            self.service_order.date_scheduled + timedelta(hours=2)
        )
        self.assertFalse(available)  # No debería estar disponible por la orden de servicio programada
        
        # Encontrar siguiente espacio disponible
        next_slot = hr_integration.find_next_available_slot(self.technician, 2.0)
        self.assertTrue(next_slot)
        self.assertGreater(next_slot[0], self.service_order.date_scheduled)
    
    def test_stock_integration(self):
        """Probar integración de inventario"""
        stock_integration = self.env['stock.integration']
        
        # Crear un producto almacenable
        stock_product = self.env['product.product'].create({
            'name': 'Test Stock Product',
            'type': 'product',
            'lst_price': 50.0,
        })
        
        # Crear un quant para el producto
        location = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        self.env['stock.quant'].create({
            'product_id': stock_product.id,
            'location_id': location.id,
            'quantity': 10.0,
        })
        
        # Verificar disponibilidad del producto
        available = stock_integration.check_product_availability(stock_product, 5.0)
        self.assertTrue(available)
        
        # Reservar producto
        move = stock_integration.reserve_product_for_service(stock_product, 5.0)
        self.assertTrue(move)
        self.assertEqual(move.product_qty, 5.0)
        
        # Consumir producto
        consume_move = stock_integration.consume_product_for_service(stock_product, 2.0, self.service_order)
        self.assertTrue(consume_move)
        self.assertEqual(consume_move.product_qty, 2.0)
        
        # Devolver producto
        return_move = stock_integration.return_product_from_service(stock_product, 1.0, self.service_order)
        self.assertTrue(return_move)
        self.assertEqual(return_move.product_qty, 1.0)
