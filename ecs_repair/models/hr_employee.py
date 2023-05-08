""" HR Employee """
from odoo import models, fields, api


class HrEmployee(models.Model):
    """ Inherit HR Employee """

    _inherit = 'hr.employee'

    employee_ref = fields.Char()

    @api.multi
    def name_get(self):
        """ Inherit Name Get """

        res = []
        for rec in self:
            name = ""
            if rec.employee_ref and rec.name:
                name = "%s_%s" % (rec.employee_ref, rec.name)
            else:
                name = super(HrEmployee, rec).name_get()
                name = name[0][1] if name else name
            res.append((rec.id, name))
        return res
