from odoo import models, fields, api, _

class AccountIntegration(models.AbstractModel):
    _name = 'account.integration'
    _description = 'Account Integration for Service Orders'
    
    def create_invoice_from_service_order(self, service_order):
        """Create an invoice from a service order"""
        if not service_order.partner_id:
            raise ValueError(_("Customer is required to create an invoice"))
        
        invoice_vals = {
            'partner_id': service_order.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_origin': service_order.name,
            'invoice_line_ids': [],
        }
        
        # Add service type as invoice line
        if service_order.service_type_id and service_order.service_type_id.product_id:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': service_order.service_type_id.product_id.id,
                'quantity': 1,
                'price_unit': service_order.service_type_id.product_id.lst_price,
            }))
        
        # Add refaction lines as invoice lines
        for line in service_order.refaction_line_ids:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
            }))
        
        invoice = self.env['account.move'].create(invoice_vals)
        service_order.write({'invoice_id': invoice.id, 'is_invoiced': True})
        
        return invoice
    
    def create_vendor_bill_for_refaction(self, refaction_line):
        """Create a vendor bill for a refaction line"""
        if not refaction_line.product_id or not refaction_line.product_id.seller_ids:
            return False
        
        vendor = refaction_line.product_id.seller_ids[0].partner_id
        bill_vals = {
            'partner_id': vendor.id,
            'move_type': 'in_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': refaction_line.product_id.id,
                'quantity': refaction_line.quantity,
                'price_unit': refaction_line.product_id.standard_price,
            })],
        }
        
        return self.env['account.move'].create(bill_vals)
