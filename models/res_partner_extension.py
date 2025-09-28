from odoo import models, fields, api

class ResPartnerExtension(models.AbstractModel):
    _name = 'res.partner.extension'
    _description = 'Partner Extension for Service Orders'
    
    is_service_customer = fields.Boolean(string='Is Service Customer', default=False)
    service_customer_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
    ], string='Service Customer Type')
    service_preference = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
    ], string='Service Preference', default='email')
    service_contact = fields.Char(string='Service Contact')
    service_phone = fields.Char(string='Service Phone')
    service_email = fields.Char(string='Service Email')
    service_order_count = fields.Integer(compute='_compute_service_order_count', string='Service Orders')
    equipment_count = fields.Integer(compute='_compute_equipment_count', string='Equipment')
    
    def _compute_service_order_count(self):
        for partner in self:
            partner.service_order_count = self.env['service.order'].search_count([
                ('partner_id', '=', partner.id)
            ])
    
    def _compute_equipment_count(self):
        for partner in self:
            partner.equipment_count = self.env['service.equipment'].search_count([
                ('partner_id', '=', partner.id)
            ])
    
    def action_view_service_orders(self):
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action
    
    def action_view_equipment(self):
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_equipment').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action
    
    @api.model
    def create(self, vals):
        partner = super().create(vals)
        if vals.get('is_service_customer'):
            # Create a default service contact if not provided
            if not vals.get('service_contact'):
                partner.service_contact = partner.name
            if not vals.get('service_phone'):
                partner.service_phone = partner.phone
            if not vals.get('service_email'):
                partner.service_email = partner.email
        return partner
