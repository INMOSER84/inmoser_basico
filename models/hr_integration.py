from odoo import models, fields, api
from datetime import datetime, timedelta

class HrIntegration(models.AbstractModel):
    _name = 'hr.integration'
    _description = 'HR Integration for Service Orders'
    
    def assign_technician_to_service_order(self, service_order):
        """Automatically assign a technician to a service order"""
        if not service_order.technician_id:
            # Find available technicians
            technicians = self.env['hr.employee'].search([
                ('is_technician', '=', True),
                ('active', '=', True)
            ])
            
            if technicians:
                # Simple assignment: take the first available technician
                # In a real scenario, this would consider availability, skills, etc.
                service_order.technician_id = technicians[0].id
                return technicians[0]
        
        return service_order.technician_id
    
    def check_technician_availability(self, technician, start_date, end_date):
        """Check if a technician is available for a given time slot"""
        # Check for overlapping service orders
        overlapping_orders = self.env['service.order'].search([
            ('technician_id', '=', technician.id),
            ('state', 'in', ['scheduled', 'in_progress']),
            ('date_scheduled', '<', end_date),
            ('date_completed', '>', start_date)
        ])
        
        return len(overlapping_orders) == 0
    
    def schedule_service_order(self, service_order, preferred_date=None):
        """Schedule a service order with an available technician"""
        if not preferred_date:
            preferred_date = fields.Datetime.now() + timedelta(days=1)
        
        # Try to assign a technician
        technician = self.assign_technician_to_service_order(service_order)
        
        if technician:
            # Check availability
            duration = service_order.service_type_id.duration or 2.0
            start_date = preferred_date
            end_date = start_date + timedelta(hours=duration)
            
            if self.check_technician_availability(technician, start_date, end_date):
                service_order.write({
                    'date_scheduled': start_date,
                    'state': 'scheduled'
                })
                return True
            else:
                # Find next available slot
                next_slot = self.find_next_available_slot(technician, duration)
                if next_slot:
                    service_order.write({
                        'date_scheduled': next_slot[0],
                        'state': 'scheduled'
                    })
                    return True
        
        return False
    
    def find_next_available_slot(self, technician, duration_hours):
        """Find the next available time slot for a technician"""
        # Get all scheduled orders for the technician
        orders = self.env['service.order'].search([
            ('technician_id', '=', technician.id),
            ('state', 'in', ['scheduled', 'in_progress']),
            ('date_scheduled', '>=', fields.Datetime.now())
        ], order='date_scheduled')
        
        # Start checking from tomorrow
        start_date = fields.Datetime.now() + timedelta(days=1)
        start_date = start_date.replace(hour=8, minute=0, second=0, microsecond=0)  # Start at 8 AM
        
        # Check for the next 7 days
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            end_date = current_date + timedelta(hours=duration_hours)
            
            if end_date.hour > 18:  # Don't schedule after 6 PM
                continue
                
            if self.check_technician_availability(technician, current_date, end_date):
                return (current_date, end_date)
        
        return None
