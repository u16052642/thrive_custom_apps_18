from thrive import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    high_school_grade = fields.Selection([
        ('grade_12', 'Grade 12'),
        ('grade_11', 'Grade 11'),
        ('grade_10', 'Grade 10'),
    ], tracking=True)
    upload_school_certificate = fields.Binary()
    psira_certificate = fields.Boolean(string='PSIRA Certificate', tracking=True)
    psira_card = fields.Boolean(string='PSIRA Card', tracking=True)
    psira_number = fields.Char(string='PSIRA Number', tracking=True)
    psira_expire_date = fields.Date(string='PSIRA Expire Date', tracking=True)
    upload_psira_certification = fields.Binary(string='Upload PSIRA Certification')
    security_certificate = fields.Boolean(string='Security Certificate', tracking=True)
    upload_security_certificate = fields.Binary(string='Upload Security Certificate')
    firearm_competency = fields.Boolean(string='Firearm Competency', tracking=True)
    upload_firearm_comp_certificate = fields.Binary(string='Upload Firearm Certificate')
    criminal_clearance = fields.Boolean(tracking=True)
    upload_criminal_clearance_certificate = fields.Binary()
    driver_license = fields.Boolean(string="Driver's License", tracking=True)
    upload_driver_license = fields.Binary(string='Upload Driver License')
    upload_all_files_as_1_package = fields.Binary(
        string='UPLOAD ALL FILES AS 1 PACKAGE'
    )
    upload_id_copy = fields.Binary(string='Upload ID Copy')
    upload_passport_copy = fields.Binary()
    paye_ref = fields.Char(string='PAYE REF', tracking=True, default='N/A')
    uif_ref = fields.Char(string='UIF REF', tracking=True, default='N/A')
