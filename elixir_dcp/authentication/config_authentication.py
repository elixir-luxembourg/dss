# coding=utf-8

from . import Authentication
from .. import app

__author__ = 'Valentin Grouès'

logger = app.logger


class ConfigAuthentication(Authentication):

    def __init__(self, login_password_dict):
        self.login_password_dict = login_password_dict
        logger.info("ConfigAuthentication initialized")

    def authenticate_user(self, username, password):
        expected_password = self.login_password_dict.get(username, None)
        return expected_password is not None and expected_password == password
