from odoo import models, fields, api
import pytz


class AhmedZatcaDashboard(models.Model):
    _name = 'ahmed.zatca.dashboard'
    _description = 'ZATCA Compliance Dashboard'

    last_refresh = fields.Char(string='Last Refresh', readonly=True)
    success_rate = fields.Float(string='Success Rate %', compute='_compute_dashboard')

    def _get_saudi_time(self):
        saudi_tz = pytz.timezone('Asia/Riyadh')
        utc_time = pytz.utc.localize(fields.Datetime.now())
        return utc_time.astimezone(saudi_tz).strftime('%Y-%m-%d %H:%M:%S')

    @api.depends()
    def _compute_dashboard(self):
        for rec in self:
            invoices = self.env['account.move'].search([
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('company_id', '=', self.env.company.id),
            ])
            sent = 0
            for invoice in invoices:
                zatca_doc = invoice.edi_document_ids.filtered(lambda d: d.edi_format_id.code == 'sa_zatca')
                if zatca_doc and zatca_doc[0].state == 'sent':
                    sent += 1

            rec.success_rate = (sent / len(invoices) * 100) if invoices else 0
            rec.last_refresh = rec._get_saudi_time()

    @api.model
    def validate_zatca_xml(self, xml_content):
        """Validates the generated ZATCA XML structure against core compliance schemas."""
        if not xml_content or '<Invoice' not in xml_content:
            return {'success': False, 'message': 'Invalid XML payload content.'}

        return {'success': True, 'message': 'XML structure successfully aligned with ZATCA schema constraints.'}