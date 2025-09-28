from odoo import models, fields, api

class ServiceCompleteWizard(models.TransientModel):
    _name = 'service.complete.wizard'
    _description = 'Service Complete Wizard'
    
    order_id = fields.Many2one('service.order', string='Service Order', required=True)
    completion_date = fields.Datetime(string='Completion Date', default=fields.Datetime.now, required=True)
    notes = fields.Text(string='Completion Notes')
    line_ids = fields.One2many('service.complete.wizard.line', 'wizard_id', string='Refaction Lines')
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'service.order':
            order = self.env['service.order'].browse(self.env.context['active_id'])
            res['order_id'] = order.id
            
            # Create default lines from existing refaction lines
            lines = []
            for line in order.refaction_line_ids:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'notes': line.notes,
                }))
            res['line_ids'] = lines
        return res
    
    def action_complete(self):
        self.ensure_one()
        
        # Update refaction lines
        for line in self.line_ids:
            if not line.exists():
                # Create new refaction line
                self.env['service.order.refaction.line'].create({
                    'order_id': self.order_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'notes': line.notes,
                })
            else:
                # Update existing refaction line
                line.write({
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'notes': line.notes,
                })
        
        # Complete the service order
        self.order_id.write({
            'date_completed': self.completion_date,
            'notes': self.notes,
            'state': 'completed'
        })
        
        # Send notification
        template = self.env.ref('inmoser_service_order.email_template_service_completed')
        if template:
            template.send_mail(self.order_id.id)
        
        return {'type': 'ir.actions.act_window_close'}
