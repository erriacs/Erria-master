""" IrActionsServer """
from odoo import models, api, fields

class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'


    groups_id = fields.Many2many('res.groups', 'ir_act_server_group_rel', 'server_id', 'group_id', string='Groups')
