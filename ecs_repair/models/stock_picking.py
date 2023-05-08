'''stock.picking'''
from odoo import models, fields


class StockPicking(models.Model):
    '''inherit stock.picking'''

    _inherit = 'stock.picking'

    employee_id = fields.Many2one('hr.employee')
    return_work_order_id = fields.Many2one('repair.work.order')
    work_order_id = fields.Many2one('repair.work.order')


class StockPickingType(models.Model):
    '''inherit stock.picking.type'''

    _inherit = 'stock.picking.type'

    return_repair = fields.Boolean('Used to Return broken component from repairs?')
    repair = fields.Boolean()
