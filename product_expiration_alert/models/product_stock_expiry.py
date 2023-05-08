# -*- encoding: utf-8 -*-
from ast import literal_eval
from odoo import api, models


class IrCron(models.Model):
    _inherit = 'ir.cron'

    @api.model
    def product_stock_expiration_send_email(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        user_ids = literal_eval(get_param('product_expiration_alert.notification_user_ids'))
        if user_ids:
            ctx = {}
            email_list = [user.email for user in \
                          self.env['res.users'].search([('id', 'in', user_ids)])]
            if email_list:
                ctx['email_to'] = ','.join([email for email in email_list if email])
                ctx['email_from'] = self.env.user.email
                ctx['send_email'] = True
                template = self.env.ref(
                    'product_expiration_alert.email_template_product_stock_expiration')
                template.with_context(ctx).send_mail(
                    self.id, force_send=True, raise_exception=False)
                return True
