""" Product """
from odoo import fields, models


class ProductTemplate(models.Model):
    """ Inherit product.template """

    _inherit = 'product.template'

    dimension = fields.Char()
    part_number_generation = fields.Boolean()
    repair_ok = fields.Boolean("Can be Repaired")
    return_required = fields.Boolean()
