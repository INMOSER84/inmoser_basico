from odoo import models, fields, api

class ServiceOrderWizard(models.TransientModel):
    _name = 'inmoser.service.order.wizard'
    _description = 'Service Order Mass Assignment Wizard'

    technician_id = fields.Many2one(
        'hr.employee',
        string='Technician',
        domain="[('x_inmoser_is_technician', '=', True)]",
        required=True
    )
    
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        required=True
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    
    order_count = fields.Integer(
        string='Orders to Affect',
        default=0
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            res['order_count'] = len(self.env.context['active_ids'])
        return res

    def action_assign_orders(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('No orders selected.'))
        
        orders = self.env['inmoser.service.order'].browse(active_ids)
        
        # Update orders
        orders.write({
            'assigned_technician_id': self.technician_id.id,
            'scheduled_date': self.scheduled_date,
            'priority': self.priority,
            'state': 'assigned'
        })
        
        return {'type': 'ir.actions.act_window_close'}
