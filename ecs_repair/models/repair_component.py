""" Repair Component """
from odoo import fields, models


class RepairComponent(models.Model):
    """ Define Repair Component """

    _name = 'repair.component'
    _description = 'Repair Component'
    _rec_name = 'code'

    code = fields.Char(required=True, string='Component Code')
    name = fields.Char(string='Component Name', required=True)
