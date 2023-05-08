# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class CustomMsgWiz(models.TransientModel):
    _name = "custom.msg.wiz"
    _description = "Custom Message Wizard"

    message = fields.Char()
    target_res_model = fields.Char()
    target_res_id = fields.Char()

    def ok(self):
        if self.target_res_model and self.target_res_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.target_res_model,
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': int(self.target_res_id),
                'view_id': False,
                }
