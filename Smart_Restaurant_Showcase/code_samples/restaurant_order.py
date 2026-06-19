from odoo import models, fields, api

class RestaurantOrder(models.Model):
    _name = 'restaurant.order'
    _description = 'Table Order'
    _order = 'create_date desc'

    table_id = fields.Many2one('restaurant.table', string='Table', required=True)
    state = fields.Selection([
        ('draft', 'Ordering'),
        ('submitted', 'Preparing'),
        ('completed', 'Completed'),
        ('paid', 'Paid')
    ], default='draft')

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card')
    ], string="Payment Method")

    line_ids = fields.One2many('restaurant.order.line', 'order_id', string='Order Lines')
    total_amount = fields.Float(string='Total', compute='_compute_total', store=True)

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.line_ids)

    def action_complete_order(self):
        """Finalizes lifecycle states and rotates security tokens."""
        self.state = 'completed'
        if self.table_id:
            self.table_id.generate_new_qr_token()


class RestaurantOrderLine(models.Model):
    _name = 'restaurant.order.line'
    _description = 'Order Line'

    order_id = fields.Many2one('restaurant.order')
    food_item_id = fields.Many2one('restaurant.food.item', required=True)
    addon_ids = fields.Many2many('restaurant.food.addon', string='Selected Add-ons')
    quantity = fields.Integer(default=1)
    subtotal = fields.Float(compute='_compute_subtotal')

    @api.depends('food_item_id', 'addon_ids', 'quantity')
    def _compute_subtotal(self):
        for line in self:
            base = line.food_item_id.price
            addons = sum(addon.price for addon in line.addon_ids)
            line.subtotal = (base + addons) * line.quantity