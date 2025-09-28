from odoo import models, fields, api

class ServiceReprogramWizard(models.TransientModel):
    _name = 'service.reprogram.wizard'
    _description = 'Service Reprogram Wizard'
    
    order_id = fields.Many2one('service.order', string='Service Order', required=True)
    new_date = fields.Datetime(string='New Date', required=True)
    reason = fields.Text(string='Reason', required=True)
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'service.order':
            order = self.env['service.order'].browse(self.env.context['active_id'])
            res['order_id'] = order.id
            if order.date_scheduled:
                res['new_date'] = order.date_scheduled
        return res
    
    def action_reprogram(self):
        self.ensure_one()
        
        # Check for conflicts
        business_logic = self.env['service.order.business.logic']
        temp_order = self.order_id.copy({'date_scheduled': self.new_date})
        conflicts = business_logic.check_service_order_conflicts(temp_order)
        temp_order.unlink()
        
        if conflicts:
            conflict_messages = [c['reason'] for c in conflicts]
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Scheduling Conflict'),
                    'message': '\n'.join(conflict_messages),
                    'type': 'danger',
                }
            }
        
        # Reprogram the service order
        self.order_id.write({
            'date_scheduled': self.new_date,
            'notes': f"{self.order_id.notes or ''}\n\nReprogrammed: {self.reason}",
        })
        
        # Send notification to customer
        if self.order_id.partner_id.email:
            template = self.env.ref('inmoser_service_order.email_template_service_reprogrammed')
            if template:
                template.send_mail(self.order_id.id)
        
        # Send notification to technician
        if self.order_id.technician_id.user_id:
            self.env['mail.activity'].create({
                'res_id': self.order_id.id,
                'res_model_id': self.env['ir.model']._get('service.order').id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': 'Service order reprogrammed',
                'note': f'Service order {self.order_id.name} has been reprogrammed to {self.new_date}. Reason: {self.reason}',
                'user_id': self.order_id.technician_id.user_id.id,
            })
        
        return {'type': 'ir.actions.act_window_close'}
