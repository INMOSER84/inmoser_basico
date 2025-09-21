from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class ServiceOrderPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'service_order_count' in counters:
            values['service_order_count'] = request.env['inmoser.service.order'].search_count([
                ('partner_id', '=', request.env.user.partner_id.id)
            ])
        return values

    @http.route(['/my/service_orders', '/my/service_orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_service_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        ServiceOrder = request.env['inmoser.service.order']
        domain = [('partner_id', '=', partner.id)]
        
        # Pager
        pager = portal_pager(
            url="/my/service_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=ServiceOrder.search_count(domain),
            page=page,
            step=self._items_per_page
        )
        
        orders = ServiceOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_service_orders_history'] = orders.ids[:100]
        
        values.update({
            'orders': orders,
            'page_name': 'service_order',
            'pager': pager,
            'default_url': '/my/service_orders',
        })
        return request.render("inmoser_service_order.portal_my_service_orders", values)

    @http.route(['/my/service_orders/<int:order_id>'], type='http', auth="user", website=True)
    def portal_my_service_order(self, order_id=None, **kw):
        order = request.env['inmoser.service.order'].browse(order_id)
        if order.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = {
            'order': order,
            'page_name': 'service_order',
        }
        return request.render("inmoser_service_order.portal_my_service_order", values)
