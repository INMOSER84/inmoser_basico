from odoo import models, fields, api, _

class StockIntegration(models.AbstractModel):
    _name = 'stock.integration'
    _description = 'Stock Integration for Service Orders'
    
    def check_product_availability(self, product, quantity):
        """Check if a product is available in stock"""
        quant = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0)
        ], limit=1)
        
        if quant:
            return quant.quantity >= quantity
        return False
    
    def reserve_product_for_service(self, product, quantity):
        """Reserve a product for a service order"""
        if not self.check_product_availability(product, quantity):
            return False
        
        # Find a suitable location
        location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not location:
            return False
        
        # Create a stock move
        move_vals = {
            'name': f'Reserve for service order',
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': quantity,
            'location_id': location.id,
            'location_dest_id': location.id,  # Same location for reservation
            'move_type': 'direct',
            'state': 'confirmed',
        }
        
        move = self.env['stock.move'].create(move_vals)
        move._action_confirm()
        move._action_assign()
        
        return move
    
    def consume_product_for_service(self, product, quantity, service_order):
        """Consume a product for a service order"""
        # Find a suitable location
        location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not location:
            return False
        
        # Create a stock move to consume the product
        move_vals = {
            'name': f'Consume for service order {service_order.name}',
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': quantity,
            'location_id': location.id,
            'location_dest_id': self.env.ref('stock.location_consumption').id,
            'move_type': 'direct',
            'origin': service_order.name,
            'state': 'confirmed',
        }
        
        move = self.env['stock.move'].create(move_vals)
        move._action_confirm()
        move._action_assign()
        move._action_done()
        
        return move
    
    def return_product_from_service(self, product, quantity, service_order):
        """Return a product from a service order"""
        # Find a suitable location
        location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not location:
            return False
        
        # Create a stock move to return the product
        move_vals = {
            'name': f'Return from service order {service_order.name}',
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': quantity,
            'location_id': self.env.ref('stock.location_consumption').id,
            'location_dest_id': location.id,
            'move_type': 'direct',
            'origin': service_order.name,
            'state': 'confirmed',
        }
        
        move = self.env['stock.move'].create(move_vals)
        move._action_confirm()
        move._action_assign()
        move._action_done()
        
        return move
    
    def create_picking_for_service_order(self, service_order):
        """Create a picking for a service order"""
        if not service_order.refaction_line_ids:
            return False
        
        # Find a suitable location
        location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not location:
            return False
        
        # Create picking
        picking_vals = {
            'partner_id': service_order.partner_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': location.id,
            'location_dest_id': self.env.ref('stock.location_customers').id,
            'origin': service_order.name,
            'move_type': 'direct',
        }
        
        picking = self.env['stock.picking'].create(picking_vals)
        
        # Create moves
        for line in service_order.refaction_line_ids:
            move_vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.quantity,
                'picking_id': picking.id,
                'location_id': location.id,
                'location_dest_id': self.env.ref('stock.location_customers').id,
                'state': 'confirmed',
            }
            
            self.env['stock.move'].create(move_vals)
        
        return picking
