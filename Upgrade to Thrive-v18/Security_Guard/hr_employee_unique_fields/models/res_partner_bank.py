from thrive import models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    _sql_constraints = [
        ('bank_account_unique', 'unique(acc_number, bank_id)', 'Account number must be unique per bank'),
    ]
