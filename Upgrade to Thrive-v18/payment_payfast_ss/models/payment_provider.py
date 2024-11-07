import hashlib
import logging
import urllib.parse

from thrive import api, fields, models

from thrive.addons.payment_payfast_ss import const

_logger = logging.getLogger(__name__)


class PaymentAcquirerPayFast(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("payfast", "PayFast Payment")],
        ondelete={"payfast": "set default"},
    )
    payfast_merchant_id = fields.Char(string="Merchant ID")
    payfast_merchant_key = fields.Char(string="Merchant Key")
    payfast_merchant_passphrase = fields.Char(string="Merchant Passphrase")

    def get_payfast_api_url(self):
        self.ensure_one()
        if self.state == "enabled":
            return "https://www.payfast.co.za"
        else:
            return "https://sandbox.payfast.co.za"

    def _payfast_generate_signature(self, params):
        self.ensure_one()
        passPhrase = self.payfast_merchant_passphrase
        payload = ""
        for key in params:
            payload += (
                key + "=" + urllib.parse.quote_plus(params[key].replace("+", " ")) + "&"
            )
        payload = payload[:-1]
        if passPhrase != "":
            payload += f"&passphrase={passPhrase}"
        return hashlib.md5(payload.encode()).hexdigest()

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """Override of payment to unlist acquirers for unsupported currencies."""
        providers = super()._get_compatible_acquirers(
            *args, currency_id=currency_id, **kwargs
        )

        currency = self.env["res.currency"].browse(currency_id).exists()
        if currency and currency.name not in ["ZAR"]:
            providers = providers.filtered(lambda a: a.code not in ["payfast"])
        return providers

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code not in ["payfast"]:
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
