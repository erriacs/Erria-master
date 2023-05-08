# -- coding: utf-8 --
{
    'name': 'Repair Tariff Fast Duplication – Erria',
    'version': '12.0.1.0',
    'sequence': 1,
    'category': 'repair',
    'summary': 'Repair Tariff fast duplication through SQL for Erria',
    'author': 'Công Ty TNHH Port Cities Việt Nam',
    'website': 'https://www.portcities.vn',
    'depends': [
        'repair', 'hr',
        'ecs_stock', 'ecs_repair'
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/tariff_sql_install.xml',
        'wizard/custom_message_views.xml',
        'wizard/repair_tariff_copy_lines.xml',
        'views/repair_tariff_view.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False
}
