from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceType(models.Model):
    _name = 'inmoser.service.type'
    _description = 'Service Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Service Type',
        required=True,
        translate=True
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        copy=False
    )
    
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    active = fields.Boolean(
        default=True
    )
    
    estimated_duration = fields.Float(
        string='Estimated Duration (hours)',
        help="Average time required to complete this service type"
    )
    
    standard_price = fields.Float(
        string='Standard Price',
        digits='Product Price'
    )
    
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'service_type_id',
        string='Service Orders'
    )
    
    service_order_count = fields.Integer(
        compute='_compute_service_order_count',
        string='Service Orders Count'
    )
    
    @api.depends('service_order_ids')
    def _compute_service_order_count(self):
        for service_type in self:
            service_type.service_order_count = len(service_type.service_order_ids)

    @api.constrains('code')
    def _check_unique_code(self):
        for service_type in self:
            if self.search([('code', '=', service_type.code), ('id', '!=', service_type.id)]):
                raise ValidationError(_('Service type code must be unique.'))

    def action_view_service_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('inmoser_service_order.action_service_order')
        action['domain'] = [('service_type_id', '=', self.id)]
        action['context'] = {'default_service_type_id': self.id}
        return action
