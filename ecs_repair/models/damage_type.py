""" Damage Type """
from odoo import fields, models


class DamageType(models.Model):
    """ Damage Type """

    _name = 'damage.type'
    _description = 'Damage Type'
    _rec_name = 'code'

    code = fields.Char('Damage Code', required=True)
    name = fields.Char('Damage Description', required=True)
    component_ids = fields.Many2many('repair.component',
                                     'damage_type_component_rel',
                                     'damage_id',
                                     'component_id',
                                     string='Component Code')
    location_ids = fields.Many2many('repair.location',
                                    'damage_type_location_rel',
                                    'damage_id',
                                    'location_id',
                                    string='Location Code')
