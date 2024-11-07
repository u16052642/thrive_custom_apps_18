from thrive import models, fields


class HRContract(models.Model):
    _inherit = 'hr.contract'

    f_3699_gross_remuneration = fields.Monetary(
        currency_field='currency_id',
        string='3699 Gross Remuneration (Total Gross for 12 months)',
    )
    f_4103_total_employee_tax = fields.Monetary(
        currency_field='currency_id',
        string='4103 Total Employee Tax',
    )
    f_4005_medical_aid_contributions = fields.Monetary(
        currency_field='currency_id',
        string='4005 Medical Aid Contributions',
    )
    f_4001_pension_fund_current = fields.Monetary(
        currency_field='currency_id',
        string='4001 Pension Fund Current',
    )
