import logging

from werkzeug import urls

from thrive import _, api, models
from thrive.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code not in ["payfast"]:
            return res
        base_api_url = self.provider_id.get_payfast_api_url()
        api_url = urls.url_join(base_api_url, "/eng/process")
        partner_sudo = (
            self.env["res.partner"].sudo().browse(processing_values.get("partner_id"))
        )
        payfast_merchant_id = self.provider_id.payfast_merchant_id
        payfast_merchant_key = self.provider_id.payfast_merchant_key
        base_url = self.env.company.get_base_url()
        # ngrok url to test in local
        # base_url = "https://d5f9-2405-201-200d-285a-ad2b-2ef6-ef8b-9d07.ngrok-free.app"
        return_url = urls.url_join(base_url, "/payment/payfast/return")
        cancel_url = urls.url_join(base_url, "/payment/payfast/cancel")
        notify_url = urls.url_join(base_url, "/payment/payfast/notify")
        amount = processing_values["amount"]
        m_payment_id = processing_values["reference"]

        sale_order = (
            self.env["sale.order"]
            .sudo()
            .search([("name", "=", m_payment_id.split("-")[0].strip())])
        )
        if sale_order:
            item_names = [
                line.product_id.name if line.product_id else " "
                for line in sale_order.order_line
            ]
        else:
            invoice = (
                self.env["account.move"]
                .sudo()
                .search([("name", "=", m_payment_id.split("-")[0].strip())])
            )
            item_names = [
                line.product_id.name if line.product_id else " "
                for line in invoice.invoice_line_ids
            ]
        item_name = ", ".join(item_names) if len(item_names) > 0 else " "
        params = {
            "merchant_id": payfast_merchant_id,
            "merchant_key": payfast_merchant_key,
            "return_url": return_url,
            "cancel_url": cancel_url,
            "notify_url": notify_url,
            "name_first": partner_sudo.name,
            "email_address": partner_sudo.email if partner_sudo.email else " ",
            "m_payment_id": m_payment_id,
            "amount": str(amount),
            "item_name": item_name,
        }
        signature = self.provider_id._payfast_generate_signature(params)
        params.update({"signature": signature, "api_url": api_url})
        return params

    @api.model
    def _get_tx_from_notification_data(self, code, data):
        tx = super()._get_tx_from_notification_data(code, data)
        if code.code not in ["payfast"]:
            return tx
        reference = data.get("m_payment_id", False)
        if not reference:
            _logger.error(
                "PayFast: we cannot found transaction reference in PayFast post data"
            )
            raise ValidationError(
                _("PayFast: we cannot found transaction reference in PayFast post data")
            )
        tx = self.search(
            [("reference", "=", reference), ("provider_code", "=", code.code)]
        )
        if not tx:
            error_msg = (
                _("PayFast: No transaction found matching reference %s") % reference
            )
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = _("PayFast: %s orders found for reference %s") % (
                len(tx),
                reference,
            )
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx

    def _payfast_s2s_validate_tree(self, response):
        self.ensure_one()
        if self.state not in ("draft", "pending", "refunding"):
            _logger.info(
                "Square: trying to validate an already validated tx (ref %s)",
                self.reference,
            )
            return True

        if response.get("payment_status") == "COMPLETE":
            provider_reference = response.get("pf_payment_id")
            self.sudo().write(
                {
                    "state_message": "Payment has been successfully completed.",
                    "provider_reference": provider_reference,
                }
            )
            self._set_done()
            return True
        else:
            error_message = "Payment has been declined"
            _logger.warning(error_message)
            provider_reference = response.get("pf_payment_id") or response.get(
                "m_payment_id"
            )
            self.sudo().write(
                {
                    "state_message": error_message,
                    "provider_reference": provider_reference,
                }
            )
            self._set_error(error_message)
            return False

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code not in ["payfast"]:
            return

        return self._payfast_s2s_validate_tree(data)
