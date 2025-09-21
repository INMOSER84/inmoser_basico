from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class ServiceOrder(models.Model):
    _name = 'inmoser.service.order'
    _description = 'Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name desc'

    name = fields.Char(
        string='Order Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    equipment_id = fields.Many2one(
        'inmoser.service.equipment',
        string='Equipment',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    service_type_id = fields.Many2one(
        'inmoser.service.type',
        string='Service Type',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    reported_fault = fields.Text(
        string='Reported Fault',
        required=True,
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('pending_approval', 'Pending Approval'),
        ('accepted', 'Accepted'),
        ('rescheduled', 'Rescheduled'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    
    assigned_technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        domain="[('x_inmoser_is_technician', '=', True)]",
        ondelete='set null',
        tracking=True
    )
    
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        tracking=True
    )
    
    diagnosis = fields.Text(
        string='Diagnosis',
        tracking=True
    )
    
    work_performed = fields.Text(
        string='Work Performed',
        tracking=True
    )
    
    customer_signature = fields.Binary(
        string='Customer Signature'
    )
    
    acceptance_status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], string='Acceptance Status', default='pending', tracking=True)
    
    photo_before = fields.Binary(
        string='Photo Before Service'
    )
    
    photo_after = fields.Binary(
        string='Photo After Service'
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        copy=False,
        readonly=True
    )
    
    total_amount = fields.Float(
        string='Total Amount',
        digits='Product Price',
        compute='_compute_total_amount',
        store=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    
    notes = fields.Text(
        string='Internal Notes'
    )
    
    refaction_line_ids = fields.One2many(
        'inmoser.service.order.refaction.line',
        'order_id',
        string='Refaction Lines'
    )
    
    duration = fields.Float(
        string='Duration (hours)',
        compute='_compute_duration',
        store=True
    )
    
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        store=True
    )
    
    @api.depends('scheduled_date')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for order in self:
            order.is_overdue = order.scheduled_date and order.scheduled_date < now and order.state not in ['done', 'cancelled']

    @api.depends('refaction_line_ids.total_price')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.total_price for line in order.refaction_line_ids)

    @api.depends('create_date', 'write_date')
    def _compute_duration(self):
        for order in self:
            if order.create_date and order.write_date and order.state == 'done':
                delta = order.write_date - order.create_date
                order.duration = delta.total_seconds() / 3600  # Convert to hours
            else:
                order.duration = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inmoser.service.order') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals:
            for order in self:
                order._track_state_change(vals['state'])
        return super().write(vals)

    def _track_state_change(self, new_state):
        self.ensure_one()
        # Add activity or send notification based on state change
        if new_state == 'assigned' and self.assigned_technician_id.user_id:
            self.activity_schedule(
                'inmoser_service_order.mail_act_service_assigned',
                user_id=self.assigned_technician_id.user_id.id,
                note=f'Service order {self.name} has been assigned to you.'
            )

    def action_assign(self):
        for order in self:
            if not order.assigned_technician_id:
                raise UserError(_('Please assign a technician before changing state.'))
            if not order.scheduled_date:
                raise UserError(_('Please schedule a date before changing state.'))
            order.write({'state': 'assigned'})

    def action_start_progress(self):
        self.write({'state': 'in_progress'})

    def action_request_approval(self):
        self.write({'state': 'pending_approval'})

    def action_accept(self):
        self.write({'acceptance_status': 'accepted', 'state': 'accepted'})

    def action_reject(self):
        self.write({'acceptance_status': 'rejected', 'state': 'draft'})

    def action_complete(self):
        for order in self:
            if not order.work_performed:
                raise UserError(_('Please describe the work performed before completing.'))
            order.write({'state': 'done'})

    def action_reschedule(self):
        self.write({'state': 'rescheduled'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_invoice(self):
        self.ensure_one()
        # Implementation for invoice creation
        pass

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for order in self:
            if order.scheduled_date and order.scheduled_date < fields.Datetime.now():
                raise ValidationError(_('Scheduled date cannot be in the past.'))

    @api.constrains('assigned_technician_id', 'scheduled_date')
    def _check_technician_availability(self):
        for order in self:
            if order.assigned_technician_id and order.scheduled_date:
                # Check if technician has overlapping orders
                overlapping_orders = self.search([
                    ('assigned_technician_id', '=', order.assigned_technician_id.id),
                    ('scheduled_date', '=', order.scheduled_date),
                    ('state', 'not in', ['done', 'cancelled']),
                    ('id', '!=', order.id)
                ])
                if overlapping_orders:
                    raise ValidationError(_('Technician already has an order scheduled at this time.'))
