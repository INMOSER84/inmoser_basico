# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging

_logger = logging.getLogger(__name__)


class HrEmployeeExtension(models.Model):
    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Campos específicos para técnicos
    # ------------------------------------------------------------------
    x_inmoser_is_technician = fields.Boolean(
        string='Is Technician',
        help='Indica si este empleado es un técnico de servicio',
        default=False
    )

    x_inmoser_virtual_warehouse_id = fields.Many2one(
        'stock.location',
        string='Virtual Warehouse',
        help='Ubicación de inventario para el almacén virtual del técnico',
        domain=[('usage', '=', 'internal')]
    )

    x_inmoser_available_hours = fields.Char(
        string='Available Hours',
        help='Horas disponibles del técnico (ej: 10-12,12-14,15-17)',
        default='10-12,12-14,15-17'
    )

    x_inmoser_technician_level = fields.Selection([
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('expert', 'Expert'),
        ('specialist', 'Specialist')
    ], string='Technician Level', help='Nivel de experiencia del técnico')

    x_inmoser_specialties = fields.Text(
        string='Specialties',
        help='Especialidades y certificaciones del técnico'
    )

    x_inmoser_max_daily_orders = fields.Integer(
        string='Max Daily Orders',
        help='Número máximo de órdenes de servicio por día',
        default=4
    )

    # Relaciones
    x_inmoser_assigned_orders = fields.One2many(
        'inmoser.service.order',
        'assigned_technician_id',
        string='Assigned Service Orders',
        help='Órdenes de servicio asignadas a este técnico'
    )

    # Campos computados
    x_inmoser_active_orders_count = fields.Integer(
        string='Active Orders Count',
        compute='_compute_active_orders_count',
        store=True,
        help='Número de órdenes activas asignadas'
    )

    x_inmoser_completed_orders_count = fields.Integer(
        string='Completed Orders Count',
        compute='_compute_completed_orders_count',
        store=True,
        help='Número de órdenes completadas'
    )

    total_service_hours = fields.Float(
        string='Total Service Hours',
        compute='_compute_service_hours',
        store=True
    )

    monthly_service_hours = fields.Float(
        string='Monthly Service Hours',
        compute='_compute_service_hours',
        store=True
    )

    service_efficiency = fields.Float(
        string='Service Efficiency (%)',
        compute='_compute_service_hours',
        store=True
    )

    avg_service_rating = fields.Float(
        string='Average Service Rating',
        compute='_compute_avg_service_rating',
        store=True
    )

    # ------------------------------------------------------------------
    # Métodos computados
    # ------------------------------------------------------------------
    @api.depends('x_inmoser_assigned_orders.state')
    def _compute_active_orders_count(self):
        for employee in self:
            if employee.x_inmoser_is_technician:
                active_states = ['assigned', 'in_progress', 'pending_approval', 'accepted']
                employee.x_inmoser_active_orders_count = len(
                    employee.x_inmoser_assigned_orders.filtered(lambda o: o.state in active_states)
                )
            else:
                employee.x_inmoser_active_orders_count = 0

    @api.depends('x_inmoser_assigned_orders.state')
    def _compute_completed_orders_count(self):
        for employee in self:
            if employee.x_inmoser_is_technician:
                employee.x_inmoser_completed_orders_count = len(
                    employee.x_inmoser_assigned_orders.filtered(lambda o: o.state == 'done')
                )
            else:
                employee.x_inmoser_completed_orders_count = 0

    @api.depends('x_inmoser_assigned_orders.scheduled_date', 'x_inmoser_assigned_orders.state')
    def _compute_service_hours(self):
        from datetime import datetime
        for employee in self:
            total = 0.0
            monthly = 0.0
            now = datetime.now()
            for order in employee.x_inmoser_assigned_orders:
                if order.state in ['done', 'in_progress']:
                    hours = order.total_hours if hasattr(order, 'total_hours') else 2
                    total += hours
                    if order.scheduled_date and order.scheduled_date.month == now.month and order.scheduled_date.year == now.year:
                        monthly += hours
            employee.total_service_hours = total
            employee.monthly_service_hours = monthly
            employee.service_efficiency = (employee.x_inmoser_completed_orders_count / total * 100) if total else 0

    @api.depends('x_inmoser_assigned_orders.rating')
    def _compute_avg_service_rating(self):
        for employee in self:
            ratings = [o.rating for o in employee.x_inmoser_assigned_orders if hasattr(o, 'rating') and o.rating]
            employee.avg_service_rating = sum(ratings) / len(ratings) if ratings else 0

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    @api.constrains('x_inmoser_available_hours')
    def _check_available_hours_format(self):
        for employee in self:
            if employee.x_inmoser_available_hours and employee.x_inmoser_is_technician:
                hours_pattern = r'^(\d{1,2}-\d{1,2})(,\d{1,2}-\d{1,2})*$'
                if not re.match(hours_pattern, employee.x_inmoser_available_hours):
                    raise ValidationError(_(
                        'Formato de horas no válido. Use: HH-HH,HH-HH (ej: 10-12,12-14,15-17)'
                    ))
                hours_ranges = employee.x_inmoser_available_hours.split(',')
                for hour_range in hours_ranges:
                    start_hour, end_hour = map(int, hour_range.split('-'))
                    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
                        raise ValidationError(_('Las horas deben estar entre 0 y 23.'))
                    if start_hour >= end_hour:
                        raise ValidationError(_('La hora de inicio debe ser menor que la de fin.'))

    @api.constrains('x_inmoser_max_daily_orders')
    def _check_max_daily_orders(self):
        for employee in self:
            if employee.x_inmoser_is_technician and employee.x_inmoser_max_daily_orders <= 0:
                raise ValidationError(_('El número máximo de órdenes diarias debe ser mayor que cero.'))

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange('x_inmoser_is_technician')
    def _onchange_is_technician(self):
        if not self.x_inmoser_is_technician:
            self.x_inmoser_virtual_warehouse_id = False
            self.x_inmoser_available_hours = False
            self.x_inmoser_technician_level = False
            self.x_inmoser_specialties = False
            self.x_inmoser_max_daily_orders = 0

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def action_view_assigned_orders(self):
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order').read()[0]
        action['domain'] = [('assigned_technician_id', '=', self.id)]
        action['context'] = {'default_assigned_technician_id': self.id}
        return action

    def action_view_technician_calendar(self):
        self.ensure_one()
        action = self.env.ref('inmoser_service_order.action_service_order_calendar').read()[0]
        action['domain'] = [('assigned_technician_id', '=', self.id)]
        action['context'] = {'default_assigned_technician_id': self.id}
        return action

    def action_view_completed_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Completed Orders',
            'res_model': 'inmoser.service.order',
            'view_mode': 'tree,form',
            'domain': [('assigned_technician_id', '=', self.id), ('state', '=', 'done')],
            'context': {'default_assigned_technician_id': self.id},
        }

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------
    def get_available_time_slots(self, date):
        self.ensure_one()
        if not self.x_inmoser_is_technician or not self.x_inmoser_available_hours:
            return []

        existing_orders = self.x_inmoser_assigned_orders.filtered(
            lambda o: o.scheduled_date and o.scheduled_date.date() == date and o.state not in ['cancelled', 'done']
        )

        available_slots = []
        for hour_range in self.x_inmoser_available_hours.split(','):
            start_hour, end_hour = map(int, hour_range.split('-'))
            available_slots.append((start_hour, end_hour))

        occupied_hours = []
        for order in existing_orders:
            order_hour = order.scheduled_date.hour
            occupied_hours.extend([order_hour, order_hour + 1])

        free_slots = []
        for start_hour, end_hour in available_slots:
            for hour in range(start_hour, end_hour, 2):
                if hour not in occupied_hours and hour + 1 not in occupied_hours:
                    free_slots.append((hour, hour + 2))

        return free_slots

    def check_daily_capacity(self, date):
        self.ensure_one()
        if not self.x_inmoser_is_technician:
            return False
        orders_count = len(self.x_inmoser_assigned_orders.filtered(
            lambda o: o.scheduled_date and o.scheduled_date.date() == date and o.state not in ['cancelled', 'done']
        ))
        return orders_count < self.x_inmoser_max_daily_orders

    @api.model
    def get_available_technicians(self, date, service_type=None):
        technicians = self.search([('x_inmoser_is_technician', '=', True)])
        available_techs = self.env['hr.employee']
        for tech in technicians:
            if tech.check_daily_capacity(date) and tech.get_available_time_slots(date):
                available_techs |= tech
        return available_techs

    # ------------------------------------------------------------------
    # name_get
    # ------------------------------------------------------------------
    def name_get(self):
        result = []
        for employee in self:
            name = employee.name or ''
            if employee.x_inmoser_is_technician:
                level = dict(employee._fields['x_inmoser_technician_level'].selection).get(
                    employee.x_inmoser_technician_level, ''
                )
                if level:
                    name = f"{name} ({level})"
            result.append((employee.id, name))
        return result

