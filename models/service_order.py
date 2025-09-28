from odoo import models, fields, api, _
from datetime import datetime, timedelta

class ServiceOrder(models.Model):
    _name = 'service.order'
    _description = 'Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_requested desc'
    
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    service_type_id = fields.Many2one('service.type', string='Service Type', required=True, tracking=True)
    equipment_id = fields.Many2one('service.equipment', string='Equipment', tracking=True)
    technician_id = fields.Many2one('hr.employee', string='Technician', tracking=True)
    date_requested = fields.Datetime(string='Requested Date', default=fields.Datetime.now, required=True)
    date_scheduled = fields.Datetime(string='Scheduled Date')
    date_started = fields.Datetime(string='Start Date')
    date_completed = fields.Datetime(string='Completion Date')
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='medium', tracking=True)
    refaction_line_ids = fields.One2many('service.order.refaction.line', 'order_id', string='Refaction Lines')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    is_invoiced = fields.Boolean(string='Invoiced', default=False)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)
    qr_code = fields.Binary(string='QR Code', compute='_generate_qr_code')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('service.order') or _('New')
        return super().create(vals)
    
    @api.depends('date_started', 'date_completed')
    def _compute_duration(self):
        for order in self:
            if order.date_started and order.date_completed:
                delta = order.date_completed - order.date_started
                order.duration = delta.total_seconds() / 3600  # Convert to hours
    
    def _generate_qr_code(self):
        for order in self:
            try:
                import qrcode
                import io
                import base64
                
                qr_data = f"{order.name}|{order.partner_id.name}|{order.date_requested}"
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
                
                order.qr_code = img_str
            except Exception as e:
                # Si hay un error, no generamos el código QR
                order.qr_code = False
    
    def action_schedule(self):
        for order in self:
            if not order.technician_id:
                # Assign a technician
                self.env['hr.integration'].assign_technician_to_service_order(order)
            
            if not order.date_scheduled:
                # Schedule the service order
                self.env['hr.integration'].schedule_service_order(order)
            else:
                order.write({'state': 'scheduled'})
        
        return True
    
    def action_start(self):
        for order in self:
            order.write({
                'state': 'in_progress',
                'date_started': fields.Datetime.now()
            })
        return True
    
    def action_complete(self):
        self.ensure_one()
        return {
            'name': _('Complete Service Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'service.complete.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }
    
    def action_cancel(self):
        for order in self:
            order.write({'state': 'cancelled'})
        return True
    
    def action_reprogram(self):
        self.ensure_one()
        return {
            'name': _('Reprogram Service Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'service.reprogram.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }
    
    def action_create_invoice(self):
        for order in self:
            if not order.is_invoiced:
                self.env['account.integration'].create_invoice_from_service_order(order)
        return True
    
    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
        }
    
    def action_print_service_order(self):
        self.ensure_one()
        return self.env.ref('inmoser_service_order.action_report_service_order').report_action(self)
    
    def action_print_service_certificate(self):
        self.ensure_one()
        return self.env.ref('inmoser_service_order.action_report_service_certificate').report_action(self)
    
    def _send_service_reminders(self):
        """Send reminders for upcoming service orders"""
        today = fields.Datetime.now()
        reminder_date = today + timedelta(days=1)  # Remind 1 day before
        
        upcoming_orders = self.search([
            ('date_scheduled', '<=', reminder_date),
            ('date_scheduled', '>=', today),
            ('state', '=', 'scheduled'),
        ])
        
        for order in upcoming_orders:
            # Send notification to customer
            if order.partner_id.email:
                template = self.env.ref('inmoser_service_order.email_template_service_scheduled')
                if template:
                    template.send_mail(order.id)
            
            # Create activity for technician
            if order.technician_id.user_id:
                self.env['mail.activity'].create({
                    'res_id': order.id,
                    'res_model_id': self.env['ir.model']._get('service.order').id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': 'Service order reminder',
                    'note': f'Service order {order.name} is scheduled for {order.date_scheduled}',
                    'user_id': order.technician_id.user_id.id,
                })
