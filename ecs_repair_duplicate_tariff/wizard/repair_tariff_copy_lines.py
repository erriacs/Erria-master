# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class RepairTariffCopyLinesWizard(models.TransientModel):
    _name = "repair.tariff.copy.lines.wizard"
    _description = "Repair Tariff Copy Lines Wizard"

    def _get_target(self):
        tariff_object = self.env['repair.tariff']
        tariff = tariff_object.browse(self._context.get('active_ids')[0])
        return tariff

    source_id = fields.Many2one('repair.tariff', 'Source Tariff', help='Source tariff to copy the lines from', required=True, ondelete='cascade')
    target_id = fields.Many2one('repair.tariff', 'Target Tariff', help='Target tariff to copy the lines to from the source tariff', default=_get_target, required=True, ondelete='cascade')
    target_sts_value = fields.Float(default=lambda self: self.target_id.sts_value or 0.0)

    @api.onchange('target_id')
    def _onchange_target_id(self):
        self.target_sts_value = self.target_id.sts_value

    def copy_tariff_lines(self):
        self.env['repair.tariff'].check_models()
        if not self.source_id:
            raise ValidationError(_("You need to choose which source tariff to copy the lines from first!"))
        if not self.target_id:
            raise ValidationError(_("You need to choose which target tariff to copy the lines to first!"))
        Tariffs = self.env['repair.tariff.line.duplication']
        vals = {
            'source_id': self.source_id.id,
            'target_id': self.target_id.id,
            'target_sts_value': self.target_sts_value,
            }
        start = datetime.now()
        _logger.info("Duplication of lines from %s to %s started" % (self.source_id.name, self.target_id.name))
        Tariffs.create(vals)
        end = datetime.now()
        duration = end - start
        start_str = start.strftime('%Y-%m-%d %H:%M:%S.') + '%03d' % (round(start.microsecond/1000))
        end_str = end.strftime('%Y-%m-%d %H:%M:%S.') + '%03d' % (round(end.microsecond/1000))
        duration_str = '%d.%03d' % (duration.seconds, round(duration.microseconds/1000))

        message = _("Duplication of lines from source tariff <strong>%s</strong> to target tariff <strong>%s</strong> started at <strong>%s</strong> and finished at <strong>%s</strong>.<br/>The duration was <strong>%s</strong> seconds.") % (self.source_id.name, self.target_id.name, start_str, end_str, duration_str)
        message_log = "Duplication of lines from %s to %s started at %s and finished at %s; duration %ss" % (self.source_id.name, self.target_id.name, start_str, end_str, duration_str)
        _logger.info(message_log)
        return self.pop_custom_message(message, self.target_id.id)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'repair.tariff',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.target_id.id,
            'view_id': False,
        }

    @api.model
    def pop_custom_message(self, msg, target_res_id=False):
        view_id = self.env.ref('ecs_repair_duplicate_tariff.custom_message_view_form').id
        return {'type': 'ir.actions.act_window',
                'name': _('Server Message'),
                'res_model': 'custom.msg.wiz',
                'target': 'new',
                'context': {
                    'default_message': msg,
                    'default_target_res_model': 'repair.tariff',
                    'default_target_res_id': target_res_id,
                    },
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[view_id, 'form']],
        }
