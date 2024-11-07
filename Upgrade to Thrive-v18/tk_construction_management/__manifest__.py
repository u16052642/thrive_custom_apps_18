# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
{
    'name': "Construction Management | Job Costing | BOQ | Work Orders | RA Billing | Material Purchase Requisition | Construction Sub Contracting | Job Order | Job Sheet | Construction Budget",
    'description': """
        - Construction Management
        - BOQ
        - Rate Analysis
        - RA Billing
        - Job Costing 
        - Job Cost Sheet
        - Job Contract
        - Project Site
        - Construction Project Management
        - Job Budget Management
        - Construction Scrape Management
        - Construction Waste Management
    """,
    'summary': """Advance Construction Management""",
    'version': "2.0.6",
    'author': 'TechKhedut Inc.',
    'company': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'website': "https://www.techkhedut.com",
    'support': "info@techkhedut.com",
    'category': 'Industry',
    'depends': ['mail', 'contacts', 'stock', 'hr', 'purchase', 'project', 'hr_timesheet'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        # Data
        'data/sequence.xml',
        'data/construction_data.xml',
        'data/construction_report_paperformat.xml',
        # wizard
        'wizard/site_project_view.xml',
        'wizard/project_warehouse_view.xml',
        'wizard/requisition_reject_view.xml',
        'wizard/import_material_view.xml',
        'wizard/budget_construction_view.xml',
        'wizard/project_wbs_view.xml',
        'wizard/wbs_entries_view.xml',
        # views
        'views/assets.xml',
        'views/construction_site_view.xml',
        'views/res_partner_view.xml',
        'views/document_view.xml',
        'views/construction_configuration_view.xml',
        'views/construction_project_view.xml',
        'views/construction_department_view.xml',
        'views/purchase_stock_inherit_view.xml',
        'views/job_costing_view.xml',
        'views/job_order_view.xml',
        'views/material_requisition_view.xml',
        'views/construction_product_template_view.xml',
        'views/internal_transfer_view.xml',
        'views/construction_project_task_view.xml',
        'views/scrap_order_view.xml',
        'views/project_budget_view.xml',
        'views/construction_res_user_view_inherit.xml',
        'views/res_config_views.xml',
        'views/sub_contract_view.xml',
        'views/quality_check_view.xml',
        'views/rate_analysis_view.xml',
        # Menus
        'views/menus.xml',
        # Reports
        'report/work_completion_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tk_construction_management/static/src/xml/template.xml',
            'tk_construction_management/static/src/css/lib/dashboard.css',
            'tk_construction_management/static/src/css/lib/style.css',
            'tk_construction_management/static/src/css/style.scss',
            'tk_construction_management/static/src/js/construction_owl.js',
        ],
    },
    'images': ['static/description/cover.gif'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 399,
    'currency': 'USD',
}
