from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import qrcode
import io
import base64

class ServiceEquipment(models.Model):
    _name = 'inmoser.service.equipment'
    _description = 'Service Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Equipment ID',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    
    equipment_type = fields.Char(
        string='Equipment Type',
        required=True,
        tracking=True
    )
    
    brand = fields.Char(
        string='Brand',
        required=True,
        tracking=True
    )
    
    model = fields.Char(
        string='Model',
        tracking=True
    )
    
    serial_number = fields.Char(
        string='Serial Number',
        copy=False,
        tracking=True
    )
    
    location = fields.Char(
        string='Location',
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    qr_code = fields.Binary(
        string='QR Code',
        compute='_generate_qr_code',
        store=True
    )
    
    qr_code_text = fields.Char(
        string='QR Code Text',
        compute='_compute_qr_code_text',
        store=True
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'equipment_id',
        string='Service Orders'
    )
    
    service_order_count = fields.Integer(
        compute='_compute_service_order_count',
        string='Service Orders Count'
    )
    
    last_service_date = fields.Datetime(
        compute='_compute_last_service_date',
        string='Last Service Date',
        store=True
    )
    
    @api.depends('service_order_ids', 'service_order_ids.state')
    def _compute_service_order_count(self):
        for equipment in self:
            equipment.service_order_count = len(equipment.service_order_ids.filtered(lambda o: o.state != 'cancelled'))

    @api.depends('service_order_ids', 'service_order_ids.write_date')
    def _compute_last_service_date(self):
        for equipment in self:
            orders = equipment.service_order_ids.filtered(lambda o: o.state == 'done')
            equipment.last_service_date = max(orders.mapped('write_date')) if orders else False

    @api.depends('name', 'partner_id.x_inmoser_client_sequence')
    def _compute_qr_code_text(self):
        for equipment in self:
            if equipment.name and equipment.name != _('New') and equipment.partner_id.x_inmoser_client_sequence:
                equipment.qr_code_text = f"{equipment.partner_id.x_inmoser_client_sequence}-{equipment.name}"
            else:
                equipment.qr_code_text = False

    @api.depends('qr_code_text')
    def _generate_qr_code(self):
        for equipment in self:
            if equipment.qr_code_text:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(equipment.qr_code_text)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                equipment.qr_code = base64.b64encode(buffer.getvalue())
            else:
                equipment.qr_code = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.equipment') or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': _('New'),
            'serial_number': False,
            'qr_code': False,
            'qr_code_text': False
        })
        return super().copy(default)

    @api.constrains('serial_number')
    def _check_unique_serial_number(self):
        for equipment in self:
            if equipment.serial_number:
                existing = self.search([
                    ('serial_number', '=', equipment.serial_number),
                    ('id', '!=', equipment.id)
                ])
                if existing:
                    raise ValidationError(_('Serial number must be unique per equipment.'))

    def action_view_service_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('inmoser_service_order.action_service_order')
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {'default_equipment_id': self.id}
        return action
