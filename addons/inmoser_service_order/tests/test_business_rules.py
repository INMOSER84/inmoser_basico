from odoo.tests.common import TransactionCase
from datetime import date, timedelta


class TestBusinessRules(TransactionCase):

    def test_overdue_calculation(self):
        Order = self.env['inmoser.service.order']
        partner = self.env['res.partner'].create({'name': 'P'})
        equipment = self.env['inmoser.service.equipment'].create({
            'name': 'E', 'partner_id': partner.id})
        service_type = self.env['inmoser.service.type'].create({'name': 'ST'})

        old_order = Order.create({
            'partner_id': partner.id,
            'equipment_id': equipment.id,
            'service_type_id': service_type.id,
            'scheduled_date': date.today() - timedelta(days=5),
            'reported_fault': 'old',
        })
        self.assertTrue(old_order.is_overdue)
