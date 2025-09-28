from odoo import models, fields, api

class HrEmployeeExtension(models.AbstractModel):
    _name = 'hr.employee.extension'
    _description = 'HR Employee Extension for Service Orders'
    
    is_technician = fields.Boolean(string='Is Technician', default=False)
    technician_code = fields.Char(string='Technician Code')
    specialization = fields.Char(string='Specialization')
    certification = fields.Char(string='Certification')
    certification_date = fields.Date(string='Certification Date')
    certification_expiry = fields.Date(string='Certification Expiry')
    service_order_count = fields.Integer(compute='_compute_service_order_count', string='Service Orders')
    
    def _compute_service_order_count(self):
        for employee in self:
            employee.service_order_count = self.env['service.order'].search_count([
                ('technician_id', '=', employee.id)
            ])
    
    def action_view_service_orders(self):
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('technician_id', '=', self.id)]
        action['context'] = {'default_technician_id': self.id}
        return action
    
    def check_certification_validity(self):
        """Check if certification is still valid"""
        for employee in self:
            if employee.certification_expiry and employee.certification_expiry < fields.Date.today():
                # Send notification to manager
                manager = employee.parent_id or employee.department_id.manager_id
                if manager:
                    self.env['mail.thread'].message_notify(
                        partner_ids=manager.partner_id.ids,
                        subject=f"Certification Expired for {employee.name}",
                        body=f"The certification for {employee.name} has expired on {employee.certification_expiry}."
                    )
