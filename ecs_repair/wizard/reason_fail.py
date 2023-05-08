from odoo import models, fields, api, _
from pprint import pprint

class ReasonQCFail(models.TransientModel):
    """ Inherit Reason QC Fail"""
    _name = 'reason.qc.fail'

    repair_id = fields.Many2one('repair.order', string="Repair")
    detail_reason = fields.Text('Reason Detail', translate=True)


    def create_reason(self):
        active_id = self._context and self._context.get('active_id')
        obj_id = self._context and self.env[self._context.get('active_model')].browse(active_id)
        obj_id.action_fail_qc()
        obj_id.write({
            'detail_reason': self.detail_reason,
            'state': 'rework'
            })
        