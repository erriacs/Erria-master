""" Partner """
from odoo import models, fields


class ResPartner(models.Model):
    """ Inherit res partner """

    _inherit = 'res.partner'

    vendor_location = fields.Selection([('Domestic', 'Domestic'),
                                        ('Foreign', 'Foreign')])
    price_term = fields.Selection([('Landed', 'Landed'),
                                   ('FOB', 'FOB')])

class ResPartnerBank(models.Model):
    """ Inherit res partner bank """

    _inherit = 'res.partner.bank'

    bank_branch = fields.Char(string="Branch")
