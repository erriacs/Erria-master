""" Repair Tariff """
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_resource
from math import ceil
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class RepairTariff(models.Model):
    """ Inherit Repair Tariff """

    _inherit = 'repair.tariff'


    tariff_line_ids = fields.One2many(copy=False)

    @api.model
    def pop_custom_message(self, msg):
        view_id = self.env.ref('ecs_repair_duplicate_tariff.custom_message_view_form').id
        return {'type': 'ir.actions.act_window',
                'name': _('Server Message'),
                'res_model': 'custom.msg.wiz',
                'target': 'new',
                'context': {'default_message': msg},
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[view_id, 'form']],
        }

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy_lines_orm(self, default=None):
        self.ensure_one()
        """ Committed copying of tariff_line_ids through ORM - target: 0.5M+ lines in a record
            Scrubbed - too slow - a batch of 500 records takes about 1 minute on my localhost """
        new = super(RepairTariff, self).copy(default=default)

        # copying tariff_line_ids in batches with commits
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ': Copying records started')
        records_per_commit = 500 # 50000
        Lines = self.env['repair.tariff.line']
        number_of_records = len(self.tariff_line_ids)
        number_of_iterations = ceil(number_of_records/records_per_commit)
        for i in range(number_of_iterations):
            offset = (i * records_per_commit)
            lines_current = Lines.search([('tariff_id', '=', self.id)], \
                offset=offset, limit=records_per_commit)
            # lines = [(0, 0, line.copy_data()[0]) for line in lines_current]
            lines_ = [line.copy_data()[0] for line in lines_current]
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ': copy_data() finished')
            lines = [(0, 0, line) for line in lines_]
            new.write({'tariff_line_ids': lines})
            if number_of_iterations > 1:
                self.env.cr.commit()
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f' Duplicated tariff_line_ids {offset+1} - {min(offset + records_per_commit, number_of_records)}')

        return new

    def copy_lines_sql(self, default=None):
        """ Special copy that copies tariff lines directly through SQL query
            Scrubbed - faster than ORM, but still not efficient enough; the speed plummets with growing number of records in database """
        self.ensure_one()
        self.check_models()
        tariff_line_ids = False
        if default:
            default['tariff_line_ids'] = tariff_line_ids
        else:
            default = {'tariff_line_ids': tariff_line_ids}
        new = super(RepairTariff, self).copy(default=default)
        cr = self.env.cr
        cr.commit()
        user_id = self.env.user.id
        sql = """
INSERT INTO repair_tariff_line (tariff_id, name, component_id, location_id, damage_type,
    repair_type_id, length, width, repair_code, quantity, sts, labour_price, material_price,
    price_subtotal, create_uid, create_date, write_uid, write_date, mode_id, origin_id)
SELECT %s "tariff_id", name, component_id, location_id, damage_type, repair_type_id, length,
    width, repair_code, quantity, sts, labour_price, material_price, price_subtotal,
    %s "create_uid", NOW() AT TIME ZONE 'UTC' "create_date", %s "write_uid",
    NOW() AT TIME ZONE 'UTC' "write_date", mode_id, id "origin_id"
FROM repair_tariff_line
WHERE tariff_id = %s;

INSERT INTO tariff_line_material (tariff_line_id, name, product_id, quantity, uom_id, create_uid,
    create_date, write_uid, write_date)
SELECT ln.id "tariff_line_id", m.name, m.product_id, m.quantity, m.uom_id, ln.create_uid,
    ln.create_date, ln.write_uid, ln.write_date
FROM repair_tariff_line lo
INNER JOIN tariff_line_material m ON lo.id = m.tariff_line_id
LEFT JOIN repair_tariff_line ln ON ln.origin_id = lo.id
WHERE lo.tariff_id = %s AND ln.tariff_id = %s;

INSERT INTO tariff_line_tax_rel (tariff_line_id, tax_id)
SELECT ln.id "tariff_line_id", t.tax_id
FROM  repair_tariff_line lo
INNER JOIN tariff_line_tax_rel t ON lo.id = t.tariff_line_id
LEFT JOIN repair_tariff_line ln ON ln.origin_id = lo.id
WHERE lo.tariff_id = %s AND ln.tariff_id = %s;
        """
        _logger.info('Copying lines started')
        cr.execute(sql, (
            new.id, user_id, user_id, self.id, # tariff lines
            self.id, new.id, # materials
            self.id, new.id, # taxes
            ))
        _logger.info('Copying lines finished')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'repair.tariff',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': new.id,
            'view_id': False,
        }

    @api.model
    def check_models(self):
        """ Raises an error if fields in models affected by SQL manipulations are changed """
        problems = []
        line = self.env['repair.tariff.line'].fields_get()
        material = self.env['tariff.line.material'].fields_get()
        fields = {
            'line': [
                '__last_update', 'display_name', 'id', 'tariff_id', 'name', 'component_id', 'location_id', 'damage_type', 'repair_type_id', 'length', 'width', 'repair_code', 'quantity', 'sts', 'labour_price', 'material_price', 'price_subtotal', 'create_uid', 'create_date', 'write_uid', 'write_date', 'mode_id', 'origin_id', 'material_line_ids', 'partner_id', 'tax_ids', #'tax_ids_duplication'
                ],
            'material': [
                '__last_update', 'display_name', 'id', 'tariff_line_id', 'name', 'product_id', 'quantity', 'uom_id', 'create_uid', 'create_date', 'write_uid', 'write_date',
                ],
        }

        # TODO do this in a cycle with parametrized problem lines
        if len(line) != len(fields['line']):
            problems.append(_("The 'Repair Tariff Line' model was changed. Fields were added or removed."))
        for field in fields['line']:
            if field not in line:
                problems.append(_("The field '%s' of the 'Repair Tariff Line' model was removed.") % field)
        for field in line:
            if field not in fields['line']:
                problems.append(_("The field '%s' of the 'Repair Tariff Line' model was added.") % field)

        if len(material) != len(fields['material']):
            problems.append(_("The 'Repair Tariff Line Material' model was changed. Fields were added or removed."))
        for field in fields['material']:
            if field not in material:
                problems.append(_("The field '%s' of the 'Repair Tariff Line Material' model was removed.") % field)
        for field in material:
            if field not in fields['material']:
                problems.append(_("The field '%s' of the 'Repair Tariff Line Material' model was added.") % field)

        if problems:
            # If this error shows to the customer, please update all SQL in this module (including data/install.sql) and add/remove field names in the 'fields' dict in this function so that it follows the current state, and update the following error message and the module description with the current date.
            error = _("The 'Repair Tariff Line' or 'Repair Tariff Line Material' model was changed. This action relies on their state from 05/03/2020 and the module 'ecs_repair_duplicate_tariff' must be updated. Please contact support.\n\nFound problems:\n")
            for problem in problems:
                error += problem + "\n"
            raise UserError(error)

        return True

    @api.model
    def _install_SQL(self):
        self.check_models()
        sql_file_path = get_module_resource('ecs_repair_duplicate_tariff', 'data/', 'install.sql')
        with open(sql_file_path, 'r') as file:
            sql = file.read()
        self.env.cr.execute(sql)
        _logger.info("SQL duplication: Function and trigger installed")

    def write(self, vals):
        """ Overridden to recalculate lines' labour price and subtotal by SQL if STS Value changed """
        self.check_models()
        sql = ''
        sql_params = []
        for tariff in self:
            if 'sts_value' in vals and float(vals['sts_value']) != tariff.sts_value:
                sql += '''
UPDATE repair_tariff_line
SET
    labour_price = sts * %s,
    price_subtotal = sts * %s + material_price
WHERE tariff_id = %s;
                '''
                sql_params.append(float(vals['sts_value']))
                sql_params.append(float(vals['sts_value']))
                sql_params.append(tariff.id)
        res = super(RepairTariff, self).write(vals)
        if sql_params:
            start = datetime.now()
            _logger.info("Updating lines with STS %.2f started" % (vals['sts_value']))

            self.env.cr.execute(sql, sql_params)

            end = datetime.now()
            duration = end - start
            start_str = start.strftime('%Y-%m-%d %H:%M:%S.') + '%03d' % (round(start.microsecond/1000))
            end_str = end.strftime('%Y-%m-%d %H:%M:%S.') + '%03d' % (round(end.microsecond/1000))
            duration_str = '%d.%03d' % (duration.seconds, round(duration.microseconds/1000))

            message_log = "Updating lines with STS %.2f started at %s and finished at %s; duration %ss" % (vals['sts_value'], start_str, end_str, duration_str)
            _logger.info(message_log)

            if len(sql_params) == 3:
                message = _("Updating lines of tariff <strong>%s</strong> with new STS Value <strong>%.2f</strong> started at <strong>%s</strong> and finished at <strong>%s</strong>.<br/>The duration was <strong>%s</strong> seconds.") % (self.name, self.sts_value, start_str, end_str, duration_str)
                return self.pop_custom_message(message)
            else:
                message = _("Updating lines with new STS Value <strong>%.2f</strong> started at <strong>%s</strong> and finished at <strong>%s</strong>.<br/>The duration was <strong>%s</strong> seconds.") % (vals['sts_value'], start_str, end_str, duration_str)
                return self.pop_custom_message(message)
        return res


class RepairTariffLine(models.Model):
    """ Inherit Repair Tariff Line """

    _inherit = 'repair.tariff.line'

    origin_id = fields.Many2one('repair.tariff.line', copy=False, help='Technical field helping with duplication of Tariff through SQL. Temporarily keeps ID of the line it was copied from.')

    # Overriding the compute function
    labour_price = fields.Float(compute="_compute_labour_price_new")

    def validateLine(self, tariff_id, quantity, name, limit=1, id=None):
        Line = self.env['repair.tariff.line']
        query = [['tariff_id', '=', tariff_id], ['quantity', '=', quantity], ['name', '=', name]]
        if id:
            query.append(['id', '!=', id])
        same = Line.search(query)
        if (len(same) > limit):
            return _('\nThe line %s with quantity %s already exists.') % (name, quantity)
        return False

    @api.model
    def validateLines(self, tariff_id=None, quantity=None, name=None, limit=1):
        error_start = _('Quantity and Combined Code of a line must be unique in one tariff.\n')
        error_body = ''
        if tariff_id != None or quantity != None or name != None:
            self.ensure_one()
            tariff_id = tariff_id or self.tariff_id.id
            quantity = quantity or self.quantity
            name = name or self.name
            error_body += (self.validateLine(tariff_id, quantity, name, limit) or '')
        else:
            for line in self:
                error_body += (self.validateLine(line.tariff_id.id, line.quantity, line.name, limit - 1, line.id) or '')
        if error_body != '':
            message = error_start + error_body
            raise ValidationError(message)

    @api.multi
    @api.constrains('tariff_id', 'quantity', 'name')
    def _check_uniqueness(self):
        self.validateLines()

    @api.model
    def pop_custom_message(self, msg):
        view_id = self.env.ref('ecs_repair_duplicate_tariff.custom_message_view_form').id
        return {'type': 'ir.actions.act_window',
                'name': _('Server Message'),
                'res_model': 'custom.msg.wiz',
                'target': 'new',
                'context': {'default_message': msg},
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[view_id, 'form']],
        }

    def _compute_labour_price(self):
        """ 
            Overridden to skip calculation - cannot override the @api.depends decorator to exclude calculation on tariff_id.sts_value change (overriding @api.depends actually concatenates the old and new filed list).
            Also overridden the field with new compute function, this is here just for good measure.
            The recalculation of lines on sts_value change is done by SQL when write() is called so it works even with tariffs that have a large amount of lines.
        """

        return

    @api.depends('sts')
    def _compute_labour_price_new(self):
        """
            Recalculates labour price if sts changed
            #, but not on too many lines
            #If the limit becomes an issue, consider adding a function to do this by SQL instead
        """

        # if len(self) > 50:
        #     # message = _("There are %d lines to have Labour Price and Price Before Taxes recalculated. It will be done when you save the tariff.") % (len(self))
        #     # return self.pop_custom_message(message)
        #     return
        # else:
        #     for line in self:
        #         line.labour_price = line.sts * line.tariff_id.sts_value
        for line in self:
            line.labour_price = line.sts * line.tariff_id.sts_value


class RepairTariffLineDuplication(models.Model):
    """ Repair tariff - table for duplication trigger """

    _name = 'repair.tariff.line.duplication'
    _description = 'Repair Tariff - table for copying tariff lines from one tariff to another. After a source_id and target_id pair is put here from a tariff, PostgreSQL runs the repair_tariff_line_duplication() function.'

    source_id = fields.Many2one('repair.tariff', required=True)
    target_id = fields.Many2one('repair.tariff', required=True)
    target_sts_value = fields.Float()
