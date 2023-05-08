""" Repair Types """
from odoo import fields, models


class RepairTypes(models.Model):
    """ Define Repair Types """

    _name = 'repair.types'
    _rec_name = 'code'
    _description = 'Repair Types'

    code = fields.Char('Type Code', required=True)
    name = fields.Char('Type Description', required=True)
    component_ids = fields.Many2many('repair.component',
                                     'repair_type_component_rel',
                                     'type_id',
                                     'component_id',
                                     string='Component Code')
    location_ids = fields.Many2many('repair.location',
                                    'repair_type_location_rel',
                                    'type_id',
                                    'location_id',
                                    string='Location Code')
    damage_ids = fields.Many2many('damage.type',
                                  'repair_type_damage_rel',
                                  'type_id',
                                  'damage_id',
                                  string='Damage Code')
