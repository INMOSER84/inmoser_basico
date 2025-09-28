from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestServiceOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ServiceOrder = cls.env['inmoser.service.order']
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Prueba'})
        cls.equipment = cls.env['inmoser.service.equipment'].create({
            'name': 'Equipo Demo',
            'partner_id': cls.partner.id,
        })
        cls.technician = cls.env['hr.employee'].create({
            'name': 'Técnico Demo',
            'x_inmoser_is_technician': True,
        })
        cls.service_type = cls.env['inmoser.service.type'].create({'name': 'Mantenimiento'})

    def test_create_order(self):
        order = self.ServiceOrder.create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'assigned_technician_id': self.technician.id,
            'service_type_id': self.service_type.id,
            'scheduled_date': date.today() + timedelta(days=1),
            'reported_fault': 'No enciende',
        })
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.name.startswith('SO'), True)

    def test_action_assign(self):
        order = self.ServiceOrder.create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'scheduled_date': date.today(),
            'reported_fault': 'Fallo test',
        })
        order.action_assign_technician()
        self.assertEqual(order.state, 'assigned')

    def test_refaction_constraint(self):
        order = self.ServiceOrder.create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'service_type_id': self.service_type.id,
            'scheduled_date': date.today(),
            'reported_fault': 'Test',
        })
        # negative qty should raise
        with self.assertRaises(ValidationError):
            order.write({
                'refaction_line_ids': [(0, 0, {
                    'product_id': self.env['product.product'].search([], limit=1).id or 1,
                    'quantity': -5,
                })]
            })
