import hashlib
import logging
import pprint
import socket
import urllib.parse

import requests
from werkzeug import urls

from thrive import _, http
from thrive.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PayFastController(http.Controller):
    _notify_url = "/payment/payfast/notify"

    @http.route(
        "/payment/payfast/notify",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
    )
    def payfast_notify(self, **post):
        _logger.info("PayFast: Notification data", pprint.pformat(post))
        self._payfast_validate_data(post)
        return "OK"

    @http.route(["/payment/payfast/cancel"], type="http", auth="public", csrf=False)
    def payment_payfast_notify(self, **post):
        _logger.info("PayFast: Cancel data", pprint.pformat(post))
        return http.request.redirect("/shop")

    @http.route(
        ["/payment/payfast/return"],
        type="http",
        auth="public",
        methods=["POST", "GET"],
        csrf=False,
    )
    def payment_payfast_return(self, **post):
        _logger.info("PayFast: Return data", pprint.pformat(post))
        self._payfast_validate_data(post)
        return http.request.redirect("/payment/status")

    def _payfast_validate_data(self, post):
        if not post:
            _logger.info("PayFast: received empty notification data")
            return False
        if post.get("signature") is None:
            _logger.error("PayFast: received notification data with no signature")
            return False

        provider_sudo = (
            http.request.env["payment.provider"]
            .sudo()
            .search([("code", "=", "payfast")], limit=1)
        )
        if not provider_sudo:
            raise ValidationError(_("PayFast provider not found."))

        signature_validation = self._validate_signature(post, provider_sudo)
        ip_validation = self._validate_ip(post)
        payment_data_validation = self._validate_payment_data(post)
        server_validation = self._validate_server(post, provider_sudo)
        if (
            signature_validation
            and ip_validation
            and payment_data_validation
            and server_validation
        ):
            # All checks have passed, process payment
            http.request.env["payment.transaction"].sudo()._handle_notification_data(
                provider_sudo,
                post,  # Match the transaction
            )
        else:
            # Some checks have failed, check payment manually and log for investigation
            raise ValidationError(
                _("Cannot perform PayFast Validations. Payment Processing Failed.")
            )

    def _validate_signature(self, post, provider_sudo):
        payload = self._create_signature_payload(post, provider_sudo)
        return (hashlib.md5(payload.encode()).hexdigest()) == post.get("signature")

    def _create_signature_payload(self, post, provider_sudo):
        payload = ""
        for key in post:
            if key != "signature":
                payload += (
                    key
                    + "="
                    + urllib.parse.quote_plus(post[key].replace("+", " "))
                    + "&"
                )
        payload += f"passphrase={provider_sudo.payfast_merchant_passphrase}"
        return payload

    def _validate_ip(self, post):
        valid_hosts = [
            "www.payfast.co.za",
            "sandbox.payfast.co.za",
            "w1w.payfast.co.za",
            "w2w.payfast.co.za",
        ]
        valid_ips = []

        for item in valid_hosts:
            ips = socket.gethostbyname_ex(item)
            if ips:
                for ip in ips:
                    if ip:
                        valid_ips.append(ip)
        # Remove duplicates from array
        clean_valid_ips = []
        for item in valid_ips:
            # Iterate through each variable to create one list
            if isinstance(item, list):
                for prop in item:
                    if prop not in clean_valid_ips:
                        clean_valid_ips.append(prop)
            else:
                if item not in clean_valid_ips:
                    clean_valid_ips.append(item)

        # Security Step 3, check if referrer is valid
        if (
            urls.url_parse(http.request.httprequest.headers.get("Referer")).host
            not in clean_valid_ips
        ):
            return False
        else:
            return True

    def _validate_payment_data(self, post):
        tx_sudo = (
            http.request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", post.get("item_name"))])
        )
        return not (abs(float(tx_sudo.amount)) - float(post.get("amount_gross"))) > 0.01

    def _validate_server(self, post, provider_sudo):
        provider_sudo = (
            http.request.env["payment.provider"]
            .sudo()
            .search([("code", "=", "payfast")], limit=1)
        )
        if not provider_sudo:
            _logger.error("PayFast: received notification data for unknown provider")
            return False
        payload = self._create_signature_payload(post, provider_sudo)
        api_url = provider_sudo.get_payfast_api_url()
        url = urls.url_join(api_url, "/eng/query/validate")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=60)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        ) as err:
            error = "PayFast: could not connect to PayFast server"
            _logger.error(error)
            raise ValidationError(error) from err

        return response.text == "VALID"
