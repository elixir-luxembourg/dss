# coding=utf-8
from functools import wraps
from flask import request, current_app, render_template
from flask_login.config import EXEMPT_METHODS
from flask_login import current_user


def app_authorization(**options):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if request.method in EXEMPT_METHODS:
                return func(*args, **kwargs)
            elif current_app.login_manager._login_disabled:
                return func(*args, **kwargs)
            elif  not current_user.has_role_from(options.get('allowed_roles')):
                return render_template('error.html', message="Error 403 - Unauthorized", show_home_link=True), 403
            return func(*args, **kwargs)

        return decorated_view

    return wrapper

#not current_user.is_authenticated:
#    return current_app.login_manager.unauthorized()
#elif


from . import errors
from . import web_controllers

__author__ = 'Valentin Grouès, Pinar Alper'

__all__ = [errors, web_controllers]
