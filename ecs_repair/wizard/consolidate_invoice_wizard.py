""" Consolidate Invoice Wizard """
from odoo import models, _
from odoo.exceptions import UserError


class ConsolidateInvoiceWizard(models.TransientModel):
    """ Defining consolidate invoice wizard """

    _name = "consolidate.invoice.wizard"
    _description = "Consolidate Invoice Wizard"

    def _consolidate_invoice(self, repair, sales_account):
        """ Execute consolidate invoice """

        origin = ""
        price = 0.0
        master = []
        account_id = False
        currency_id = False
        fiscal = False
        partner_id = False
        for order in repair:
            labour_price = 0.0
            material_price = 0.0
            taxes = []
            origin = order.name if not origin else "%s, %s" % (origin, order.name)
            account_id = order.partner_id.property_account_receivable_id.id
            partner_id = order.partner_invoice_id.id or order.partner_id.id
            currency_id = order.currency_id.id
            fiscal = order.partner_id.property_account_position_id.id
            for line in order.estimation_line_ids.filtered(lambda r: r.approved):
                labour_price += line.quantity * line.labour_price
                material_price += line.quantity * line.material_price
                price += line.quantity * line.labour_price + \
                    line.quantity * line.material_price
                taxes = line.tax_ids
            subtotal = order.product_qty * (labour_price + material_price)
            master_vals = {'product_id': order.product_id.id,
                           'name': order.name,
                           'repair_order_id': order.id,
                           'quantity': order.product_qty,
                           'uom_id': order.product_uom.id,
                           'container_label': order.container_label,
                           'labour_price': labour_price,
                           'material_price': material_price,
                           'price_subtotal': subtotal,
                           'tax_ids': [(6, 0, [tid.id for tid in taxes if taxes])]}
            master.append((0, 0, master_vals))
        inv_line = {'name': 'Dịch vụ sửa chữa',
                    'origin': origin,
                    'account_id': sales_account,
                    'quantity': 1,
                    'invoice_line_tax_ids': [(6, 0, [tid.id for tid in taxes if taxes])],
                    'price_unit': price,
                    'price_subtotal': 1 * price}
        invoice = self.env['account.invoice'].create({
            'name': origin,
            'origin': origin,
            'type': 'out_invoice',
            'account_id': account_id,
            'partner_id': partner_id,
            'currency_id': currency_id,
            'fiscal_position_id': fiscal,
            'invoice_line_ids': [(0, 0, inv_line)],
            'master_invoice_line_ids': master})
        invoice.compute_taxes()
        repair.write({'invoiced': True,
                      'state': 'draft_invoice',
                      'invoice_id': invoice.id})
        return True

    def consolidate_invoice(self):
        """ Consolidate invoice """

        repair = self.env['repair.order'].browse(self._context.get('active_ids', []))
        sales_account = self.env['repair.order'].with_context(
            company=repair[0].company_id.id).get_default_income_account()
        taxes = []
        for rep in repair:
            taxes += rep.estimation_line_ids.mapped('tax_ids')
        if not sales_account:
            raise UserError(_('No default income account defined for company "%s".') \
                            % repair[0].company_id.name)
        elif len(repair.mapped('partner_id')) > 1:
            raise UserError(_("Can only consolidate invoice for orders of a customer!"))
        elif len(repair.mapped('currency_id')) > 1:
            raise UserError(_("Can only consolidate invoice for orders with similar currency!"))
        elif any(state != '2binvoiced' for state in repair.mapped('state')):
            raise UserError(_("Can only consolidate invoice for to be invoiced orders!"))
        elif len(set(taxes)) > 1:
            raise UserError(_("Can only consolidate invoice for orders with similar taxes!"))
        self._consolidate_invoice(repair, sales_account)
