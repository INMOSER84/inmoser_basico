from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ServiceOrderRefactionLine(models.Model):
    _name = 'inmoser.service.order.refaction.line'
    _description = 'Service Order Refaction Line'

    order_id = fields.Many2one(
        'inmoser.service.order',
        string='Service Order',
        required=True,
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('type', '=', 'product')]",
        ondelete='restrict'
    )
    
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        required=True,
        default=1.0
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        digits='Product Price',
        required=True
    )
    
    total_price = fields.Float(
        string='Total Price',
        digits='Product Price',
        compute='_compute_total_price',
        store=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price
            self.description = self.product_id.name

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero.'))
