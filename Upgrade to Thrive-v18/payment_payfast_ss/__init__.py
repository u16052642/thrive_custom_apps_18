from . import models
from . import controllers
from thrive.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    setup_provider(env, "payfast")


def uninstall_hook(env):
    reset_payment_provider(env, "payfast")
