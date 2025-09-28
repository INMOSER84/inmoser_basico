from odoo import models, fields, api, _
from datetime import datetime, timedelta

class ServiceEquipment(models.Model):
    _name = 'service.equipment'
    _description = 'Service Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    
    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    model = fields.Char(string='Model')
    manufacturer = fields.Char(string='Manufacturer')
    purchase_date = fields.Date(string='Purchase Date')
    warranty_start = fields.Date(string='Warranty Start')
    warranty_end = fields.Date(string='Warranty End')
    partner_id = fields.Many2one('res.partner', string='Owner', required=True, tracking=True)
    location = fields.Char(string='Location')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)
    service_order_ids = fields.One2many('service.order', 'equipment_id', string='Service Orders')
    last_service_date = fields.Datetime(string='Last Service Date')
    next_service_date = fields.Datetime(string='Next Service Date')
    service_interval = fields.Integer(string='Service Interval (days)', default=365)
    qr_code = fields.Binary(string='QR Code', compute='_generate_qr_code')
    
    @api.model
    def create(self, vals):
        equipment = super().create(vals)
        
        # Schedule first service if interval is set
        if vals.get('service_interval'):
            next_service = fields.Datetime.now() + timedelta(days=vals.get('service_interval'))
            equipment.write({'next_service_date': next_service})
        
        return equipment
    
    @api.depends('name', 'serial_number', 'partner_id')
    def _generate_qr_code(self):
        for equipment in self:
            try:
                import qrcode
                import io
                import base64
                
                qr_data = f"{equipment.name}|{equipment.serial_number}|{equipment.partner_id.name}"
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue())
                
                equipment.qr_code = img_str
            except Exception as e:
                # Si hay un error, no generamos el código QR
                equipment.qr_code = False
    
    def action_schedule_service(self):
        self.ensure_one()
        return {
            'name': _('Schedule Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'service.order',
            'view_mode': 'form',
            'context': {
                'default_equipment_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }
    
    def action_view_service_history(self):
        self.ensure_one()
        return {
            'name': _('Service History'),
            'type': 'ir.actions.act_window',
            'res_model': 'service.order',
            'view_mode': 'tree,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
    
    def action_print_equipment_history(self):
        self.ensure_one()
        return self.env.ref('inmoser_service_order.action_report_equipment_history').report_action(self)
    
    def _check_warranty_expiration(self):
        """Check for equipment with expiring warranty"""
        today = fields.Date.today()
        warning_date = today + timedelta(days=30)  # Warn 30 days before expiration
        
        expiring_equipment = self.search([
            ('warranty_end', '<=', warning_date),
            ('warranty_end', '>=', today),
            ('active', '=', True)
        ])
        
        for equipment in expiring_equipment:
            # Send notification to owner
            if equipment.partner_id.email:
                template = self.env.ref('inmoser_service_order.email_template_warranty_expiration')
                if template:
                    template.send_mail(equipment.id)
            
            # Create activity for responsible person
            self.env['mail.activity'].create({
                'res_id': equipment.id,
                'res_model_id': self.env['ir.model']._get('service.equipment').id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': 'Warranty expiration notification',
                'note': f'The warranty for {equipment.name} will expire on {equipment.warranty_end}',
                'user_id': self.env.user.id,
            })
