# coding=utf-8
from functools import wraps
from flask import request, current_app, render_template
from flask_login.config import EXEMPT_METHODS
from flask_login import current_user
from elixir_dcp import db
import importlib

submission_models_module = importlib.import_module('elixir_dcp.models.submission')

def app_authorization(**options):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if request.method in EXEMPT_METHODS:
                return func(*args, **kwargs)
            elif current_app.login_manager._login_disabled:
                return func(*args, **kwargs)
            elif not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            else:
                if not current_user.has_role_from(options.get('allowed_roles')):
                    return render_template('error.html', message="Error 403 - Unauthorized", show_home_link=True), 403
                if (not current_user.is_admin()) and options.get('record_authorization'):
                    params = options.get('record_authorization')
                    my_entity_name =  getattr(submission_models_module, params['entity'])
                    my_entity_id = kwargs[params['entity_id_key']]
                    my_entity = db.session.query(my_entity_name).get(my_entity_id)
                    my_attribute = getattr(my_entity,params['entity_ac_attribute'])
                    if not has_access(current_user.get_id(), my_attribute):
                        return render_template('error.html', message="Error 403 - Unauthorized", show_home_link=True), 403
            return func(*args, **kwargs)

        return decorated_view

    return wrapper




from . import errors
from . import web_controllers
from ..models.services import has_access

__author__ = 'Valentin Grouès, Pinar Alper'

__all__ = [errors, web_controllers]
