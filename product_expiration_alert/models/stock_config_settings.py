# -*- encoding: utf-8 -*-
from ast import literal_eval
from odoo import api, fields, models


class StockSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    report_days = fields.Integer(
        string="Generate Report For(Next Days)",
        help="Number of days product will be expire in stock")
    include_expire_stock = fields.Boolean(
        help="Past and Future product stock expire report form select Include Expire Stock.")
    report_type = fields.Selection(
        [('all', 'All'), ('location', 'location')],
        string='Report Type', default='all',
        help="Filter based on location wise and all stock product expiration report")
    location_ids = fields.Many2many(
        "stock.location", string="Filter by Locations",
        help="Check Product Stock for Expiration from selected Locations only. " \
        "If its blank it checks in all Locations")
    notification_user_ids = fields.Many2many(
        "res.users", string="Notification to",
        help="Product stock expiration mail goes to Selected users")

    @api.model
    def get_values(self):
        res = super(StockSettingsInherit, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            report_days=int(get_param('product_expiration_alert.report_days')),
            report_type=get_param('product_expiration_alert.report_type'),
            include_expire_stock=get_param('product_expiration_alert.include_expire_stock'),
            location_ids=literal_eval(get_param(
                'product_expiration_alert.location_ids', default='[]')),
            notification_user_ids=literal_eval(
                get_param('product_expiration_alert.notification_user_ids', default='[]')),
            )
        return res

    @api.multi
    def set_values(self):
        res = super(StockSettingsInherit, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('product_expiration_alert.report_days', repr(self.report_days))
        set_param('product_expiration_alert.report_type', self.report_type)
        set_param('product_expiration_alert.include_expire_stock',
                  self.include_expire_stock)
        set_param('product_expiration_alert.location_ids',
                  [location for location in self.location_ids.ids])
        set_param("product_expiration_alert.notification_user_ids",
                  [user for user in self.notification_user_ids.ids])
        return res
