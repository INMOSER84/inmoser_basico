from odoo import models, fields, api

class ServiceType(models.Model):
    _name = 'service.type'
    _description = 'Service Type'
    _order = 'name'
    
    name = fields.Char(string='Service Type', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    product_id = fields.Many2one('product.product', string='Related Product')
    duration = fields.Float(string='Estimated Duration (hours)')
    equipment_required = fields.Boolean(string='Equipment Required', default=False)
    technician_required = fields.Boolean(string='Technician Required', default=True)
    service_order_count = fields.Integer(compute='_compute_service_order_count', string='Service Orders')
    
    def _compute_service_order_count(self):
        for service_type in self:
            service_type.service_order_count = self.env['service.order'].search_count([
                ('service_type_id', '=', service_type.id)
            ])
    
    def action_view_service_orders(self):
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('service_type_id', '=', self.id)]
        action['context'] = {'default_service_type_id': self.id}
        return action
