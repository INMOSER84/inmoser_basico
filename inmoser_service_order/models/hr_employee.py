from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_inmoser_is_technician = fields.Boolean(
        string='Is Technician',
        default=False
    )
    
    x_inmoser_technician_level = fields.Selection([
        ('junior', 'Junior Technician'),
        ('regular', 'Regular Technician'),
        ('senior', 'Senior Technician'),
        ('expert', 'Expert Technician')
    ], string='Technician Level')
    
    x_inmoser_technician_specialization = fields.Char(
        string='Specialization'
    )
    
    x_inmoser_technician_certifications = fields.Text(
        string='Certifications'
    )
    
    x_inmoser_technician_tools = fields.Text(
        string='Tools Assigned'
    )
    
    service_order_ids = fields.One2many(
        'inmoser.service.order',
        'assigned_technician_id',
        string='Assigned Service Orders'
    )
    
    completed_order_count = fields.Integer(
        compute='_compute_completed_order_count',
        string='Completed Orders'
    )
    
    average_completion_time = fields.Float(
        compute='_compute_performance_metrics',
        string='Average Completion Time (hours)'
    )
    
    customer_rating_avg = fields.Float(
        compute='_compute_performance_metrics',
        string='Average Customer Rating'
    )
    
    @api.depends('service_order_ids', 'service_order_ids.state', 'service_order_ids.duration')
    def _compute_completed_order_count(self):
        for employee in self:
            completed_orders = employee.service_order_ids.filtered(lambda o: o.state == 'done')
            employee.completed_order_count = len(completed_orders)

    @api.depends('service_order_ids', 'service_order_ids.state', 'service_order_ids.duration')
    def _compute_performance_metrics(self):
        for employee in self:
            completed_orders = employee.service_order_ids.filtered(lambda o: o.state == 'done')
            if completed_orders:
                employee.average_completion_time = sum(completed_orders.mapped('duration')) / len(completed_orders)
            else:
                employee.average_completion_time = 0.0
            # Customer rating calculation would require additional fields

    @api.constrains('x_inmoser_is_technician', 'user_id')
    def _check_technician_user(self):
        for employee in self:
            if employee.x_inmoser_is_technician and not employee.user_id:
                raise ValidationError(_('A technician must be linked to a user account.'))
