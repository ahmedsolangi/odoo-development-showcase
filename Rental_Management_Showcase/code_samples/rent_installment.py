from odoo import models, fields, api

class RentInstallment(models.Model):
    _name = 'rent.installment'
    _description = 'Rent Installment'
    _order = 'installment_number asc'

    installment_number = fields.Integer(string="No.", readonly=True)
    contract_id = fields.Many2one('rent.contract', string="Contract", ondelete='cascade', required=True)
    due_date = fields.Date(string="Due Date", required=True)
    amount = fields.Float(string="Amount", required=True)
    paid_amount = fields.Float(string="Paid Amount", compute='_compute_paid_amount', store=True)
    payment_history_ids = fields.One2many('installment.payment', 'installment_id', string="Payments")

    status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid')
    ], string="Status", default='pending', compute='_compute_status', store=True)

    @api.depends('payment_history_ids.amount')
    def _compute_paid_amount(self):
        for record in self:
            record.paid_amount = sum(record.payment_history_ids.mapped('amount'))

    @api.depends('paid_amount', 'amount')
    def _compute_status(self):
        for record in self:
            if record.paid_amount <= 0:
                record.status = 'pending'
            elif record.paid_amount < record.amount:
                record.status = 'partial'
            else:
                record.status = 'paid'

    def action_open_payment_wizard(self):
        """Instantiates client-side payment wizards with explicit step-down balance contexts."""
        self.ensure_one()
        return {
            'name': 'Pay Installment',
            'type': 'ir.actions.act_window',
            'res_model': 'rent.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_installment_id': self.id,
                'default_payment_amount': self.amount - self.paid_amount,
            }
        }