{
    'name': "security_upload_custom_data",
    'summary': "security_upload_custom_data",
    'description': """
    security_upload_custom_data
    """,
    'author': "BK",
    'website': "none",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['hr_payroll_account', 'planning', 'cybat_task_shift'],
    'data': [
        'data/hr_work_entry_type.xml',
        'data/planning_role.xml',
        'data/planning_slot_template.xml',
        'data/resource_calendar_leaves.xml',
        'data/task_shift.xml',
    ],
}
