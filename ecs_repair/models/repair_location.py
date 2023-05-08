""" Repair Location """
from odoo import fields, models


class RepairLocation(models.Model):
    """ Define Repair Location """

    _name = 'repair.location'
    _description = 'Repair Location'
    _rec_name = 'code'

    code = fields.Char('Location Code', required=True)
    name = fields.Char('Location', required=True)
    component_ids = fields.Many2many('repair.component',
                                     'repair_location_component_rel',
                                     'location_id',
                                     'component_id',
                                     string='Component Code')
