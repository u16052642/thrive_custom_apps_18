{
    # App information
    "name": "PayFast Payment Provider",
    "version": "17.0.1.0.2",
    "category": "Accounting/Payment Providers",
    "summary": """Payment Acquirer: Payment PayFast Integration. Do payment same way like standard Payment method availables like Paypal,Amazon,Openpay,authorize,stripe,iPay, Conekta, Pay fast. Fast pay,fastpay""",
    "license": "OPL-1",
    "depends": ["payment"],
    # Views
    "data": [
        "views/payment_payfast_template.xml",
        "data/payment_provider_data.xml",
        "views/payment_view.xml",
    ],
    "images": ["static/description/Payfast_Banner.gif"],
    # Assets
    # "assets": {
    # },
    # only loaded in demonstration mode
    "demo": [],
    # Author
    "author": "Synodica Solutions Pvt. Ltd.",
    "website": "https://synodica.com",
    "maintainer": "Synodica Solutions Pvt. Ltd.",
    "support": "support@synodica.com",
    # Technical
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "79",
    "currency": "USD",
    "uninstall_hook": "uninstall_hook",
    "post_init_hook": "post_init_hook",
}
