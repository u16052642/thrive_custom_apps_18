# -*- coding: utf-8 -*-
{
    'name': 'Xero Integration OAuth 2.0 REST API',
    'version': '0.6',
    'category': 'Accounting',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'depends': ['account', 'sale_management', 'base', 'purchase'],
    'summary': 'Xero Connector with REST API Xero Thrive Integration App xero accounting thrive xero connector thrive xero integration thrive xero accounting integration accounting app',
    'description': """
Xero Connector with REST API
============================
<keywords>
Xero Thrive Integration App
xero
xero thrive 
xero accounting
thrive xero connector
thrive xero integration
thrive xero accounting integration
accounting app
""",
    'data': [
        'views/res_company.xml',
        'views/account_account.xml',
        'views/tax.xml',
        'views/product_template.xml',
        'views/res_partner_category.xml',
        'wizard/connection_successfull_view.xml',
        'views/purchase_order.xml',
        'views/invoice.xml',
        'views/res_partner.xml',
        'views/account_payments.xml',
        'views/maintain_logs.xml',
        'views/sale_order.xml',
        'views/dashboard.xml',
        'views/xero_logger_view.xml',
        'views/automated_authentication_scheduler.xml',
        'security/ir.model.access.csv',
        'data/type_demo_data.xml',
    ],

    'images': ['static/description/thrive-xero-connector-gif.gif'],
    # 'images': ['static/description/end-of-year-sale-main.jpg'],
    # 'images': ['static/description/end_of_year_sale.gif'],
    'live_test_url': 'http://www.pragtech.co.in/company/proposal-form.html?id=103&name=Thrive-xero-Accounting-Management',
    'license': 'OPL-1',
    'price': 299.00,
    'currency': 'USD',
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'pragmatic_thrive_xero_connector/static/src/js/dashboard.js',
            'pragmatic_thrive_xero_connector/static/src/css/xero.css',
            'https://www.gstatic.com/charts/loader.js',
            'pragmatic_thrive_xero_connector/static/src/xml/dashboard.xml'
        ],
        'web.assets_frontend': [

        ],
        'web.assets_qweb': [

        ],

    },

}
