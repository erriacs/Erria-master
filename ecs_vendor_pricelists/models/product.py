""" Products """
from odoo import models, fields


class ProductSupplierInfo(models.Model):
    """ Inherit product supplier info """

    _inherit = 'product.supplierinfo'

    # vendor_location = fields.Selection(string = "Vendor Location", selection = [('Domestic', 'Domestic'), ('Foreign', 'Foreign')])
    # price_term = fields.Selection(string = "Price Term", selection = [('Landed', 'Landed'), ('FOB', 'FOB')])
    factory_price = fields.Float()
    factory_price_currency = fields.Many2one('res.currency', string='Currency')
    landed_price = fields.Float()
    landed_price_currency = fields.Many2one('res.currency', string='Currency')
    notes = fields.Text()
