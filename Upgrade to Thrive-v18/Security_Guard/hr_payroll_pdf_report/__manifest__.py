# -*- coding: utf-8 -*-
{
    'name': "hr_payroll_pdf_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['hr_payroll', 'sale', 'cybat_task_shift', 'security_custom_fields', 'hr_holidays'],
    'data': [
        # 'reports/employee_pdf_report.xml',
        'views/views.xml',
        'views/custom_pdf_report.xml',
    ],
}
