""" Account Invoice """
from odoo import models, api, fields


class MasterInvoce(models.Model):
    """ Define master invoice """

    _name = 'master.invoice'
    _description = 'Master Invoice'

    @api.depends('labour_price', 'material_price', 'account_id', 'quantity')
    def _compute_amount(self):
        """ Compute amount in line """

        for line in self:
            price_unit = line.labour_price + line.material_price
            partner = line.account_id.partner_id if line.account_id.partner_id \
                else None
            taxes = line.tax_ids.compute_all(
                price_unit,
                line.account_id.currency_id, line.quantity, None, partner)
            line.update(
                {'price_subtotal': taxes['total_excluded'],
                 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                 'price_total': taxes['total_included']})

    account_id = fields.Many2one('account.invoice', required=True,
                                 ondelete='cascade', index=True)
    container_label = fields.Char()
    currency_id = fields.Many2one('res.currency', related='account_id.currency_id')
    labour_price = fields.Monetary()
    material_price = fields.Monetary()
    name = fields.Char()
    price_subtotal = fields.Monetary(compute='_compute_amount', store=True)
    price_tax = fields.Monetary(compute='_compute_amount', store=True)
    price_total = fields.Monetary(compute='_compute_amount', store=True)
    product_id = fields.Many2one('product.product')
    quantity = fields.Float(default=1.0)
    repair_order_id = fields.Many2one('repair.order')
    tax_ids = fields.Many2many('account.tax',
                               'master_invoice_tax_rel',
                               'master_invoice_id',
                               'tax_id')
    uom_id = fields.Many2one('uom.uom')


class AccountInvoice(models.Model):
    """ Inherit account invoice """

    _inherit = 'account.invoice'

    @api.depends('master_invoice_line_ids.price_total')
    def _compute_amount_master(self):
        """ Compute sum of amount in master invoice """

        for invoice in self:
            untaxed = taxes = 0.0
            for line in invoice.master_invoice_line_ids:
                untaxed += line.price_subtotal
                taxes += line.price_tax
            invoice.update(
                {'amount_tax_master': taxes,
                 'amount_untaxed_master': untaxed,
                 'amount_total_master': taxes + untaxed})

    amount_tax_master = fields.Monetary(compute='_compute_amount_master', store=True)
    amount_total_master = fields.Monetary(compute='_compute_amount_master', store=True)
    amount_untaxed_master = fields.Monetary(compute='_compute_amount_master', store=True)
    master_invoice_line_ids = fields.One2many('master.invoice', 'account_id')
    vat_date = fields.Date()
    vat_number = fields.Char()

    @api.multi
    def invoice_validate(self):
        """ Inherit action invoice validate """

        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            # update state of repair order into invoiced
            if invoice.origin and invoice.type == 'out_invoice':
                self.env['repair.order'].sudo().update_invoice_status(invoice.origin)
        return res

    @api.multi
    def unlink(self):
        """ Inherit unlink """

        for invoice in self:
            # reverse state of repair order into 2binvoiced
            if invoice.origin and invoice.type == 'out_invoice':
                self.env['repair.order'].sudo().with_context(removed=True)\
                .update_invoice_status(invoice.origin)
        return super(AccountInvoice, self).unlink()
