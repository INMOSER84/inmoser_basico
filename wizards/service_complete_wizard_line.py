from odoo import models, fields, api

class ServiceCompleteWizardLine(models.TransientModel):
    _name = 'service.complete.wizard.line'
    _description = 'Service Complete Wizard Line'
    
    wizard_id = fields.Many2one('service.complete.wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.lst_price
        else:
            self.unit_price = 0.0
