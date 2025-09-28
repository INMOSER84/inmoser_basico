from odoo import http
from odoo.http import request

class MainController(http.Controller):
    
    @http.route(['/service-order/scan/<string:qr_data>'], type='http', auth="public", website=True)
    def scan_service_order_qr(self, qr_data=None, **kw):
        if not qr_data:
            return request.render('website.404')
        
        # Parse QR data
        try:
            parts = qr_data.split('|')
            if len(parts) < 3:
                return request.render('website.404')
            
            order_ref = parts[0]
            customer_name = parts[1]
            date_str = parts[2]
            
            # Find service order
            service_order = request.env['service.order'].search([('name', '=', order_ref)], limit=1)
            
            if not service_order:
                return request.render('website.404')
            
            # Check if the customer name matches
            if service_order.partner_id.name != customer_name:
                return request.render('website.403')
            
            values = {
                'service_order': service_order,
                'qr_data': qr_data,
            }
            
            return request.render('inmoser_service_order.service_order_qr_page', values)
        
        except Exception:
            return request.render('website.404')
    
    @http.route(['/api/service-order/<int:order_id>/status'], type='json', auth="api_key")
    def api_service_order_status(self, order_id=None, **kw):
        if not order_id:
            return {'error': 'Missing order_id'}
        
        service_order = request.env['service.order'].browse(order_id)
        
        if not service_order.exists():
            return {'error': 'Service order not found'}
        
        return {
            'id': service_order.id,
            'name': service_order.name,
            'state': service_order.state,
            'date_requested': service_order.date_requested,
            'date_scheduled': service_order.date_scheduled,
            'date_started': service_order.date_started,
            'date_completed': service_order.date_completed,
            'technician': service_order.technician_id.name if service_order.technician_id else None,
        }
    
    @http.route(['/api/service-order/<int:order_id>/update'], type='json', auth="api_key", methods=['POST'])
    def api_update_service_order(self, order_id=None, **kw):
        if not order_id:
            return {'error': 'Missing order_id'}
        
        service_order = request.env['service.order'].browse(order_id)
        
        if not service_order.exists():
            return {'error': 'Service order not found'}
        
        # Update fields based on request data
        allowed_fields = ['state', 'date_started', 'date_completed', 'notes']
        
        for field in allowed_fields:
            if field in kw:
                setattr(service_order, field, kw[field])
        
        return {
            'success': True,
            'id': service_order.id,
            'state': service_order.state,
        }
