# -*- coding: utf-8 -*-
import qrcode
import io
import base64
from odoo import http, _
from odoo.http import request, Response
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv.expression import AND


class InmoserCustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        order_count = request.env['inmoser.service.order'].sudo().search_count([('partner_id', '=', partner.id)])
        values.update({
            'service_order_count': order_count,
        })
        return values

    @http.route(['/my/services', '/my/services/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_services(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ServiceOrder = request.env['inmoser.service.order'].sudo()

        domain = [('partner_id', '=', partner.id)]

        if date_begin and date_end:
            domain += [('scheduled_date', '>=', date_begin), ('scheduled_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'scheduled_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('State'), 'order': 'state'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        order_count = ServiceOrder.search_count(domain)
        pager = portal_pager(
            url="/my/services",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )

        orders = ServiceOrder.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'orders': orders,
            'page_name': 'services',
            'pager': pager,
            'default_url': '/my/services',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("inmoser_service_order.portal_my_services", values)

    @http.route(['/my/service/<int:order_id>'], type='http', auth="public", website=True)
    def portal_service_detail(self, order_id, access_token=None, **kw):
        order = request.env['inmoser.service.order'].sudo().browse(order_id)
        if not order.exists() or (order.partner_id.id != request.env.user.partner_id.id and access_token != order.access_token):
            return request.redirect('/my')

        values = {
            'order': order,
            'page_name': 'service_detail',
        }
        return request.render("inmoser_service_order.portal_service_detail", values)

    # === QR GENERATOR ===
    @http.route('/inmoser/service/<int:order_id>/qr', type='http', auth='public', website=True, csrf=False)
    def service_qr_image(self, order_id):
        order = request.env['inmoser.service.order'].sudo().browse(order_id)
        if not order.exists():
            return Response(status=404)

        portal_url = f"{request.httprequest.host_url}my/service/{order_id}"
        img = qrcode.make(portal_url)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return Response(buffer.read(), headers={'Content-Type': 'image/png'})
