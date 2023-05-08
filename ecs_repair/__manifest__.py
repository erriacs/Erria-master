# pylint: disable=C0111,W0104
# -- coding: utf-8 --
{
    'name': 'Repair Management - Erria',
    'version': '12.0.1.0.0',
    'summary': 'Repair Management for Erria',
    'description': """
        Repair Management for Erria
    """,
    'category': 'repair',
    'author': "Portcities Ltd",
    'website': "http://www.portcities.net",
    'depends': ['repair', 'hr',
                'ecs_stock'],
    'data': [
        'security/ecs_repair_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/email_template.xml',
        'reports/repair_order_report_view.xml',
        'wizard/reason_fail_view.xml',
        'views/assets.xml',
        'views/account_invoice_view.xml',
        'views/customers_menu.xml',
        'views/damage_type_view.xml',
        'views/hr_employee_view.xml',
        'views/partner_view.xml',
        'views/repair_invoice_menu.xml',
        'views/repair_master_data_menu.xml',
        'views/repair_component_view.xml',
        'views/repair_location_view.xml',
        'views/repair_mode_view.xml',
        'views/repair_types_view.xml',
        'views/repair_tariff_view.xml',
        'views/repair_order_view.xml',
        'views/repair_order_menu.xml',
        'views/repair_work_order_view.xml',
        'views/stock_picking_view.xml',
        'views/ir_action_server.xml',
        'views/eor_report_view.xml',
        'wizard/consolidate_invoice_wizard_view.xml',
        'wizard/repair_summary_wizard_view.xml',
        'wizard/tariff_import_wizard_view.xml',
        'wizard/wizard_uploader_view.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}