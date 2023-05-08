""" Repair Tariff """
from odoo import fields, models, api, _


class RepairTariff(models.Model):
    """ Define repair tariff """

    _name = 'repair.tariff'
    _description = 'Repair Tariff Master Data'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Customer')
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.ref('base.main_company') \
                                    .currency_id)
    sts_value = fields.Float('STS Value', default=0.0)
    active = fields.Boolean(default=True)
    tariff_line_ids = fields.One2many('repair.tariff.line', 'tariff_id', copy=True)

    @api.multi
    @api.returns(None, lambda value: value[0])
    def copy_data(self, default=None):
        """ Inherit Copy Data """

        res = super(RepairTariff, self).copy_data(default=default)
        if res:
            #change name
            res[0]['name'] = _("%s (copy)") % self.name
        return res


class RepairTariffLine(models.Model):
    """ Repair tariff line """

    _name = 'repair.tariff.line'
    _description = 'Repair Tariff Line'
    _order = 'tariff_id asc'

    tariff_id = fields.Many2one('repair.tariff', required=True,
                                ondelete='cascade', index=True)
    name = fields.Char('Combined Code', compute='_compute_combined_name', store=True)
    component_id = fields.Many2one('repair.component', required=True)
    damage_type = fields.Many2one('damage.type', 'Damage', required=True)
    labour_price = fields.Float(compute="_compute_labour_price", default=1.0, store=True)
    length = fields.Float(required=True)
    location_id = fields.Many2one('repair.location', required=True)
    material_line_ids = fields.One2many('tariff.line.material', 'tariff_line_id', copy=True)
    material_price = fields.Float(default=1.0)
    mode_id = fields.Many2one('repair.mode')
    partner_id = fields.Many2one('res.partner', related='tariff_id.partner_id')
    price_subtotal = fields.Float(compute='_compute_subtotal',
                                  string='Price Before Taxes', store=True)
    quantity = fields.Float(required=True)
    repair_code = fields.Char('Customer Repair Code', require=True)
    repair_type_id = fields.Many2one('repair.types', 'Repair', required=True)
    sts = fields.Float('STS', required=True)
    tax_ids = fields.Many2many('account.tax',
                               'tariff_line_tax_rel',
                               'tariff_line_id',
                               'tax_id')
    width = fields.Float(required=True)

    @api.multi
    @api.depends('component_id', 'location_id', 'damage_type', 'repair_type_id', 'length', 'width')
    def _compute_combined_name(self):
        """ Combining name from listed code """

        for line in self:
            if line.component_id and line.location_id and line.damage_type and line.repair_type_id:
                dimension = "%s x %s" % (int(line.length), int(line.width))
                line.name = (str(line.component_id.code) + '|' +
                             str(line.location_id.code) + '|' +
                             str(line.damage_type.code) + '|' +
                             str(line.repair_type_id.code) + '|' +
                             dimension)

    @api.depends('labour_price', 'material_price')
    def _compute_subtotal(self):
        """ Compute price sub total """

        for line in self:
            line.price_subtotal = line.labour_price + line.material_price

    @api.depends('sts', 'tariff_id.sts_value')
    def _compute_labour_price(self):
        """ Compute labour price """

        for line in self:
            line.labour_price = line.sts * line.tariff_id.sts_value


class TariffLineMaterial(models.Model):
    """ Repair Tariff Line Material """

    _name = 'tariff.line.material'
    _description = 'Tariff Line Material'

    tariff_line_id = fields.Many2one(required=True,
                                     ondelete='cascade', index=True)
    name = fields.Char()
    product_id = fields.Many2one('product.product', required="1",
                                 domain="[('type', '!=', 'service')]")
    quantity = fields.Float(default=1.0)
    uom_id = fields.Many2one('uom.uom', required="1")

    @api.onchange('product_id')
    def _change_product_info(self):
        """ On change product id """

        for line in self:
            if line.product_id:
                line.update({'name': line.product_id.name,
                             'uom_id': line.product_id.uom_id.id})
