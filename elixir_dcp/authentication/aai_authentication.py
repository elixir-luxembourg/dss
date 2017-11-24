# coding=utf-8
from . import Authentication
from .. import app
from ..exceptions import AuthenticationException

__author__ = 'Valentin Grouès'

logger = app.logger


class AAIAuthentication(Authentication):

    def authenticate_user(self, username, password):
        return True


