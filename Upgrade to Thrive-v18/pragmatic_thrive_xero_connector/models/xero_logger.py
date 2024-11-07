from thrive import api, fields, models, _

class XeroLoger(models.Model):
    _name = 'xero.logger'
    _rec_name = 'thrive_name'
    _description = 'Xero Logger'

    thrive_name = fields.Char('Name')
    thrive_object = fields.Char('Object')
    message = fields.Char('Message')
    activity = fields.Char('Activity')
    xero_ref = fields.Char('Xero Ref')
    status_code = fields.Char('Status Code')
    status = fields.Selection([('failed', 'Failed'), ('done', 'Done')])