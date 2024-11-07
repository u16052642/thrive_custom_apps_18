from thrive import models, api, _


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _action_client_notify(self, title="", message="", sticky=False, notify_type='info', action_next={}):
        assert notify_type in ['info', 'success', 'warning', 'danger']

        if not action_next:
            action_next = {'type': 'ir.actions.act_window_close'}
        if not title:
            title = _("Info")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': sticky,
                'type': notify_type,
                'next': action_next
            }
        }
