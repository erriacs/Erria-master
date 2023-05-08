""" Partner """
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """ Inherit res partner """

    _inherit = 'res.partner'

    edi_partner = fields.Boolean()
    edi_email_file = fields.Char()
    edi_email_images = fields.Char()
    edi_line_ids = fields.One2many('partner.edi.line', 'partner_id')
    repair_invoice_date = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
         ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
         ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
         ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
         ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'), ('25', '25'),
         ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30')])
    repair_invoice_day = fields.Selection(
        [('6', 'Sunday'), ('0', 'Monday'), ('1', 'Tuesday'),
         ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'),
         ('5', 'Saturday')])
    repair_invoice_type = fields.Selection(
        [('weekly', 'Weekly'), ('monthly', 'Monthly'),
         ('manual', 'Manual')])

    @api.onchange('repair_invoice_type')
    def _onchange_repair_invoice_type(self):
        """ On change repair invoice type """

        for partner in self:
            if partner.repair_invoice_type == 'weekly':
                partner.update({'repair_invoice_date': False})
            elif partner.repair_invoice_type == 'monthly':
                partner.update({'repair_invoice_day': False})
            else:
                partner.update({'repair_invoice_date': False,
                                'repair_invoice_day': False})

    @api.onchange('customer')
    def _onchange_customer(self):
        """ On change customer """

        for partner in self:
            if  not partner.customer:
                partner.update({'repair_invoice_type': False,
                                'repair_invoice_date': False,
                                'repair_invoice_day': False})

    def parse_repair_to_consolidate(self, repair):
        """ Parse repair orders that will be consolidated """

        to_inv = []
        for rep in repair:
            taxes = rep.estimation_line_ids.mapped('tax_ids')
            check = [vals for vals in to_inv if to_inv \
                     and vals.get('currency_id') == rep.currency_id \
                     and vals.get('taxes') == taxes]
            if not check:
                to_inv.append({'ids': [rep.id], 'taxes': taxes,
                               'currency_id': rep.currency_id})
            else:
                check[0]['ids'].append(rep.id)
        return to_inv

    def periodic_consolidate_invoice(self):
        """ Periodic consolidate invoice """

        cur_date = fields.Date.today()
        partner = self.search([('customer', '=', True),
                               ('repair_invoice_type', 'in', ['weekly', 'monthly'])])
        for par in partner:
            if (par.repair_invoice_type == 'weekly' \
                and cur_date.weekday() == int(par.repair_invoice_day)) \
                or par.repair_invoice_type == 'monthly' \
                and cur_date.day == int(par.repair_invoice_date):

                repair = self.env['repair.order'].search(
                    [('partner_id', '=', par.id), ('state', '=', '2binvoiced')])
                if not repair:
                    continue
                to_inv = self.parse_repair_to_consolidate(repair)
                for vals in to_inv:
                    self.env['consolidate.invoice.wizard'].with_context(
                        active_ids=vals.get('ids')).consolidate_invoice()

    @api.model
    def create(self, vals):
        """ Inherit Create """

        #EDI validation
        if vals.get('edi_partner') and not vals.get('edi_line_ids'):
            raise UserError(_("Please fill value in tab EDI fields for EDI partner!"))
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        """ Inherit Write """

        #EDI validation
        res = super(ResPartner, self).write(vals)
        for partner in self:
            if partner.edi_partner and not partner.edi_line_ids:
                raise UserError(_("Please fill value in tab EDI fields for EDI partner!"))
        return res


class PartnerEdiLine(models.Model):
    """ Define Partner EDI Line """

    _name = 'partner.edi.line'
    _description = 'Partner EDI Line'

    partner_id = fields.Many2one('res.partner', required=True,
                                 ondelete='cascade', indexed=True)
    name = fields.Char()
    sequence_id = fields.Many2one('ir.sequence', required=True)
    shop_code = fields.Char(size=3, required=True)
    warehouse_id = fields.Many2one('stock.warehouse', required=True)

    @api.onchange('warehouse_id', 'shop_code')
    def _onchange_warehouse_shop(self):
        """ On change Warehouse Shop Code """

        if self.warehouse_id and self.shop_code:
            name = "%s - %s" % (self.warehouse_id.name, self.shop_code)
            self.update({'name': name})
