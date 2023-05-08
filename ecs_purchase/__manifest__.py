# coding: utf-8
{
    'name': 'ECS: Purchase Management',
    'version': '12.0.1.0.0',
    'author': 'Port Cities Vietnam',
    'website': 'http://www.portcities.vn',
    'description': """
        Custom module for Purchase for Odoo 12
    """,
    'depends': ['purchase_stock',
                'ecs_stock'],
    'data': [
        'report/ecs_purchase_quotation_templates.xml',
        'report/ecs_purchase_order_templates.xml',
        'report/purchase_reports.xml',
        'views/purchase_order.xml',
    ],
    'installable': True,
    "application": False,
    "auto_install": False,
}
