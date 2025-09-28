from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class ClientPortal(CustomerPortal):
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        ServiceOrder = request.env['service.order']
        if 'service_order_count' in counters:
            values['service_order_count'] = ServiceOrder.search_count([
                ('partner_id', '=', partner.id)
            ])
        
        return values
    
    @http.route(['/my/service-orders', '/my/service-orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_service_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        ServiceOrder = request.env['service.order']
        
        domain = [('partner_id', '=', partner.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_requested desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        
        # default sort by date
        if not sortby:
            sortby = 'date'
        
        order = searchbar_sortings[sortby]['order']
        
        # count for pager
        service_order_count = ServiceOrder.search_count(domain)
        
        # pager
        pager = portal_pager(
            url="/my/service-orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=service_order_count,
            page=page,
            step=self._items_per_page
        )
        
        # content according to pager and archive selected
        service_orders = ServiceOrder.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'date': date_begin,
            'service_orders': service_orders,
            'page_name': 'service_order',
            'pager': pager,
            'default_url': '/my/service-orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render("inmoser_service_order.portal_my_service_orders", values)
    
    @http.route(['/my/service-order/<int:service_order_id>'], type='http', auth="user", website=True)
    def portal_my_service_order(self, service_order_id=None, **kw):
        partner = request.env.user.partner_id
        service_order = request.env['service.order'].browse(service_order_id)
        
        if service_order.partner_id != partner:
            return request.redirect('/my')
        
        values = {
            'service_order': service_order,
            'page_name': 'service_order',
        }
        
        return request.render("inmoser_service_order.portal_service_order_page", values)
    
    @http.route(['/my/service-order/<int:service_order_id>/accept'], type='http', auth="user", website=True)
    def portal_accept_service_order(self, service_order_id=None, **kw):
        partner = request.env.user.partner_id
        service_order = request.env['service.order'].browse(service_order_id)
        
        if service_order.partner_id != partner:
            return request.redirect('/my')
        
        if service_order.state == 'scheduled':
            service_order.write({'state': 'in_progress'})
        
        return request.redirect(f'/my/service-order/{service_order_id}')
    
    @http.route(['/my/service-order/<int:service_order_id>/cancel'], type='http', auth="user", website=True)
    def portal_cancel_service_order(self, service_order_id=None, **kw):
        partner = request.env.user.partner_id
        service_order = request.env['service.order'].browse(service_order_id)
        
        if service_order.partner_id != partner:
            return request.redirect('/my')
        
        if service_order.state in ('draft', 'scheduled'):
            service_order.write({'state': 'cancelled'})
        
        return request.redirect(f'/my/service-order/{service_order_id}')
