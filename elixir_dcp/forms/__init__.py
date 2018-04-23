# coding=utf-8
from elixir_dcp.forms.submissions_forms import AttachmentForm, ContactForm, SubmissionForm, \
    StudyDishForm, UploadInfoForm
from elixir_dcp.models.security import Role
from wtforms import BooleanField, HiddenField, StringField, PasswordField, SelectMultipleField
from wtforms.fields.html5 import EmailField
from flask_wtf import FlaskForm
from flask import redirect, request
from urllib.parse import urlparse, urljoin
from wtforms.validators import Email, DataRequired, Length, Regexp, ValidationError
from .validators import OptionalFieldValidator

import re

__author__ = 'Pinar Alper'


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or '/'

    def redirect(self):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or '/')


class LoginForm(RedirectForm):
    """This form is for test purposes only. We use AAI IdP Proxy for logins to system.
    """
    username = EmailField('Username', [DataRequired(), Email("This field requires a valid email address")])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField('Remember me')


class SignupForm(FlaskForm):
    """This form is used to sign up users to ELIXIR DCP.
    """

    elixir_sub_id = HiddenField('Elixir Sub ID')
    first_name = StringField('First Name', validators=[DataRequired(),
                                                       Regexp('^[a-zA-Z\s]+$', message="Can only contain letters."),
                                                       Length(min=2, max=20,
                                                              message="Must be 2 to 20 characters long.")])
    last_name = StringField('Last Name',
                            validators=[DataRequired(), Regexp('^[a-zA-Z\s]+$', message="Can only contain letters."),
                                        Length(min=2, max=20, message="Must be 2 to 20 characters long.")])

    institution = StringField('Institution', validators=[DataRequired(), Regexp('^[a-zA-Z\s\(\)-]+$',
                                                                                message="Can only contain letters, parantheses and dash."),
                                                         Length(min=2, max=20,
                                                                message="Must be 2 to 20 characters long.")])

    email = EmailField('E Mail', validators=[DataRequired(), Email("Requires an email address.")],
                       render_kw={"placeholder": "Email with which ELIXIR-LU can contact you."})

    addr_line1 = StringField('Address', validators=[OptionalFieldValidator(regex_str='^[a-zA-Z0-9\s,-]+$',
                                                                           message="Can only contain letters, numbers, colon and dash.")],
                             render_kw={"placeholder": "Street Address."})

    addr_line2 = StringField('City', validators=[OptionalFieldValidator(regex_str='^[a-zA-Z0-9\s,-]+$',
                                                                        message="Can only contain letters, numbers and dash.")],
                             render_kw={"placeholder": "City, Country, Postal Code."})

    phone_no = StringField('Phone', validators=[
        OptionalFieldValidator(message="Can only contain numbers and dash.", regex_str='^[0-9\s,-]+$')])


class UserForm(SignupForm):
    """This form is used to view and edit a particular User record in the ELIXIR DCP database.
    """
    id = HiddenField('User_Id')
    assigned_role_ids = SelectMultipleField('Has Roles', coerce=int)

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.assigned_role_ids.choices = [(rol.id, rol.name) for rol in Role.query.all()]


__all__ = [SubmissionForm, ContactForm, AttachmentForm, StudyDishForm, UserForm]
