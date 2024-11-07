{
    'name': "bulk list attendance timesheet",
    'summary': "bulk list attendance timesheet",
    'description': """
    - Add 3 buttons to process multiple records.
    """,
    'author': "BK",
    'website': "https://bytekol.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['cybat_task_shift', 'planning', 'project_forecast', 'hr_attendance'],
    'data': [
        'views/planning_slot_views.xml',
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/bulk_list_attendance_timesheet/static/src/xml/*',
            '/bulk_list_attendance_timesheet/static/src/js/*',
        ],
    }
}
