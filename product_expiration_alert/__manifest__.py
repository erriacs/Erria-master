# -*- coding: utf-8 -*-
{
    'name': 'Stock Expiry Report / Notification',
    'summary': "Product Stock Expiry Report / Notification via email",
    'description': """Product Stock Expiry Report/ Notification via email""",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Warehouse',
    'version': '12.0.0.1.1',
    'depends': ['stock', 'product_expiry'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/product_stock_expiry_wiz_view.xml',
        'views/product_view.xml',
        'views/stock_config_settings_view.xml',
        'report/report_product_stock_expiry.xml',
        'report/report_action_view.xml',
        'data/product_stock_expiration_data.xml',
    ],

    'license': "OPL-1",
    'price': 25,
    'currency': "EUR",

    'auto_install': False,
    'installable': True,

    'images': ['static/description/main.png'],
}
