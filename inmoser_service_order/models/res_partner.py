from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_inmoser_client_sequence = fields.Char(
        string='Client Sequence',
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    
    x_inmoser_phone_mobile_2 = fields.Char(
        string='Secondary Mobile',
        size=32
    )
    
    x_inmoser_is_service_client = fields.Boolean(
        string='Is Service Client',
        default=False
    )
    
    x_inmoser_client_notes = fields.Text(
        string='Client Notes'
    )
    
    service_equipment_ids = fields.One2many(
        'inmoser.service.equipment',
        'partner_id',
        string='Service Equipment'
    )
    
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'partner_id',
        string='Service Orders'
    )
    
    service_order_count = fields.Integer(
        compute='_compute_service_order_count',
        string='Service Orders Count'
    )
    
    @api.depends('service_order_ids')
    def _compute_service_order_count(self):
        for partner in self:
            partner.service_order_count = len(partner.service_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('x_inmoser_client_sequence', _('New')) == _('New'):
                if vals.get('x_inmoser_is_service_client', False):
                    vals['x_inmoser_client_sequence'] = self.env['ir.sequence'].next_by_code('res.partner.x_inmoser_client_sequence') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('x_inmoser_is_service_client') and not self.x_inmoser_is_service_client:
            for partner in self:
                if not partner.x_inmoser_client_sequence or partner.x_inmoser_client_sequence == _('New'):
                    vals['x_inmoser_client_sequence'] = self.env['ir.sequence'].next_by_code('res.partner.x_inmoser_client_sequence') or _('New')
        return super().write(vals)

    @api.constrains('x_inmoser_phone_mobile_2')
    def _check_phone_mobile_2(self):
        for partner in self:
            if partner.x_inmoser_phone_mobile_2:
                if not re.match(r'^\+?[0-9\s\-\(\)]{7,}$', partner.x_inmoser_phone_mobile_2):
                    raise ValidationError(_('Please enter a valid phone number for secondary mobile.'))
