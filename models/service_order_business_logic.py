from odoo import models, fields, api, _
from datetime import datetime, timedelta

class ServiceOrderBusinessLogic(models.AbstractModel):
    _name = 'service.order.business.logic'
    _description = 'Service Order Business Logic'
    
    def validate_service_order(self, service_order):
        """Validate a service order before scheduling"""
        errors = []
        
        if not service_order.partner_id:
            errors.append(_("Customer is required"))
        
        if not service_order.service_type_id:
            errors.append(_("Service type is required"))
        
        if service_order.service_type_id.equipment_required and not service_order.equipment_id:
            errors.append(_("Equipment is required for this service type"))
        
        if service_order.service_type_id.technician_required and not service_order.technician_id:
            errors.append(_("Technician is required for this service type"))
        
        if service_order.equipment_id and service_order.equipment_id.partner_id != service_order.partner_id:
            errors.append(_("Equipment owner must match the customer"))
        
        return errors
    
    def calculate_service_duration(self, service_order):
        """Calculate the expected duration of a service order"""
        base_duration = service_order.service_type_id.duration or 0
        
        # Add time for refaction lines
        refaction_duration = 0
        for line in service_order.refaction_line_ids:
            # Assume 0.5 hours per refaction line
            refaction_duration += 0.5
        
        # Add time based on priority
        priority_factor = {
            'low': 1.0,
            'medium': 1.0,
            'high': 1.2,
            'urgent': 1.5,
        }
        
        total_duration = (base_duration + refaction_duration) * priority_factor.get(service_order.priority, 1.0)
        
        return total_duration
    
    def check_service_order_conflicts(self, service_order):
        """Check for conflicts with other service orders"""
        conflicts = []
        
        if not service_order.technician_id or not service_order.date_scheduled:
            return conflicts
        
        # Calculate expected end time
        duration = self.calculate_service_duration(service_order)
        start_time = service_order.date_scheduled
        end_time = start_time + timedelta(hours=duration)
        
        # Check for overlapping service orders
        overlapping_orders = self.env['service.order'].search([
            ('technician_id', '=', service_order.technician_id.id),
            ('id', '!=', service_order.id),
            ('state', 'in', ['scheduled', 'in_progress']),
            ('date_scheduled', '<', end_time),
            ('date_completed', '>', start_time)
        ])
        
        for order in overlapping_orders:
            conflicts.append({
                'order': order,
                'reason': _("Overlapping with service order %s") % order.name
            })
        
        # Check for equipment conflicts
        if service_order.equipment_id:
            equipment_orders = self.env['service.order'].search([
                ('equipment_id', '=', service_order.equipment_id.id),
                ('id', '!=', service_order.id),
                ('state', 'in', ['scheduled', 'in_progress']),
                ('date_scheduled', '<', end_time),
                ('date_completed', '>', start_time)
            ])
            
            for order in equipment_orders:
                conflicts.append({
                    'order': order,
                    'reason': _("Equipment conflict with service order %s") % order.name
                })
        
        return conflicts
    
    def auto_schedule_service_order(self, service_order):
        """Automatically schedule a service order"""
        # Validate first
        errors = self.validate_service_order(service_order)
        if errors:
            return {'success': False, 'errors': errors}
        
        # Assign technician if not assigned
        if not service_order.technician_id and service_order.service_type_id.technician_required:
            self.env['hr.integration'].assign_technician_to_service_order(service_order)
        
        # Find available time slot
        if not service_order.technician_id:
            return {'success': False, 'errors': [_("No technician available")]}
        
        duration = self.calculate_service_duration(service_order)
        next_slot = self.env['hr.integration'].find_next_available_slot(
            service_order.technician_id, duration
        )
        
        if not next_slot:
            return {'success': False, 'errors': [_("No available time slot found")]}
        
        # Schedule the service order
        service_order.write({
            'date_scheduled': next_slot[0],
            'state': 'scheduled'
        })
        
        return {'success': True}
    
    def generate_service_report(self, start_date, end_date):
        """Generate a service report for a given date range"""
        orders = self.env['service.order'].search([
            ('date_requested', '>=', start_date),
            ('date_requested', '<=', end_date)
        ])
        
        report_data = {
            'total_orders': len(orders),
            'completed_orders': len(orders.filtered(lambda o: o.state == 'completed')),
            'in_progress_orders': len(orders.filtered(lambda o: o.state == 'in_progress')),
            'scheduled_orders': len(orders.filtered(lambda o: o.state == 'scheduled')),
            'cancelled_orders': len(orders.filtered(lambda o: o.state == 'cancelled')),
            'total_revenue': sum(orders.filtered('is_invoiced').mapped('invoice_id.amount_total')),
            'average_duration': sum(orders.filtered('duration').mapped('duration')) / len(orders.filtered('duration')) if orders.filtered('duration') else 0,
            'technicians': {},
            'service_types': {},
        }
        
        # Group by technician
        for order in orders:
            tech = order.technician_id.name or _('Unassigned')
            if tech not in report_data['technicians']:
                report_data['technicians'][tech] = {
                    'total_orders': 0,
                    'completed_orders': 0,
                    'average_duration': 0,
                }
            
            report_data['technicians'][tech]['total_orders'] += 1
            if order.state == 'completed':
                report_data['technicians'][tech]['completed_orders'] += 1
        
        # Calculate average duration per technician
        for tech, data in report_data['technicians'].items():
            tech_orders = orders.filtered(lambda o: o.technician_id.name == tech and o.duration)
            if tech_orders:
                data['average_duration'] = sum(tech_orders.mapped('duration')) / len(tech_orders)
        
        # Group by service type
        for order in orders:
            service_type = order.service_type_id.name
            if service_type not in report_data['service_types']:
                report_data['service_types'][service_type] = 0
            
            report_data['service_types'][service_type] += 1
        
        return report_data
