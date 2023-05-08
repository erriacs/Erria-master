# coding: utf-8
{
    'name': 'ECS: Vendor Information',
    'version': '12.0.1.0.0',
    'author': 'Port Cities Vietnam',
    'website': 'http://www.portcities.vn',
    'description': """
        Custom module for Vendor information for Odoo 12
    """,
    'depends': ['contacts', 'purchase'],
    'data': ['views/partner_views.xml',],
    'installable': True,
    "application": False,
    "auto_install": False,
}
