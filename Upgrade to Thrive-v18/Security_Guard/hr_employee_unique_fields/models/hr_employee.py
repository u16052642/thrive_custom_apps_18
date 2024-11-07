from thrive import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    _sql_constraints = [
        ('identification_id_unique', 'unique(identification_id)', 'Identification must be unique'),
        ('passport_id_unique', 'unique(passport_id)', 'Passport No must be unique'),

    ]