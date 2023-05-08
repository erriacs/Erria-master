""" Repair Mode """
from odoo import fields, models


class RepairMode(models.Model):
    """ Define Repair Mode """

    _name = 'repair.mode'
    _description = 'Repair Mode'
    _rec_name = 'code'

    code = fields.Char(required=True, size=2)
    name = fields.Char(required=True)
    part_section = fields.Boolean()
