# coding=utf-8
from elixir_dcp.controllers.api_controllers import get_elu_partners
from elixir_dcp.forms.submissions_forms import AttachmentForm, ContactForm, SubmissionForm, \
    DatadecForm, UploadInfoForm, StudyForm, MessageForm
from elixir_dcp.models.security import Role
from wtforms import BooleanField, HiddenField, StringField, PasswordField, SelectMultipleField, SelectField
from wtforms.fields.html5 import EmailField
from flask_wtf import FlaskForm
from flask import redirect, request
from urllib.parse import urlparse, urljoin
from wtforms.validators import Email, DataRequired, Length, Regexp, ValidationError
from .validators import OptionalFieldValidator
from elixir_dcp import app

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
    """This form is for test/demo purposes only. We use AAI IdP Proxy for logins to system.
    """
    username = EmailField('Username', [DataRequired(), Email("This field requires a valid email address")])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField('Remember me',[DataRequired()], default=True)


class SignupForm(FlaskForm):
    """This form is used to sign up users to ELIXIR DCP.
    """

    elixir_sub_id = HiddenField('Elixir Sub ID')
    first_name = StringField('First Name',  description="Your name.", validators=[DataRequired(),
                                                       Regexp('^[\w\s]+$',
                                                              message="Can only contain letters, digits and underscore."),
                                                       Length(min=2, max=20,
                                                              message="Must be 2 to 20 characters long.")])
    last_name = StringField('Last Name', description="Your surname.",
                            validators=[DataRequired(),
                                        Regexp('^[\w\s]+$', message="Can only contain letters, digits and underscore."),
                                        Length(min=2, max=20, message="Must be 2 to 20 characters long.")])

    institution_accession = SelectField('Institution', description="Your home organisation.", validators=[DataRequired()])

    institution_division = StringField('Division/Department', description="Your division within the home organisation.",
                                       validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                          message="Can only contain letters, digits, dash, comma and dot.")])

    email = EmailField('E Mail',  description="Your institutional email.", validators=[DataRequired(), Email("Requires an email address.")],
                       render_kw={"placeholder": "Email with which ELIXIR-LU can contact you."})

    addr_line1 = StringField('Address Line 1', description="Your postal address.", validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                                  message="Can only contain letters, digits, dash, comma and dot.")],
                             render_kw={"placeholder": "Street Address."})

    addr_line2 = StringField('Address Line 2',  description="Your postal address.", validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                                  message="Can only contain letters, digits, dash, comma and dot.")],
                             render_kw={"placeholder": "City, Country, Postal Code."})

    phone_no = StringField('Phone',  description="Phone number.", validators=[
        OptionalFieldValidator(message="Can only contain digits, dash and plus.", regex_str="^[0-9\s\-\+]+$")])

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.institution_accession.choices = [(c["elu_accession"],
                                               f'{c["name"]} - {c["acronym"]}' if 'acronym' in c and c['acronym'] is not None and 'name' in c else c[
                                                   "name"] if 'name' in c else '-') for c in
                                               get_elu_partners()]


class MyProfileForm(SignupForm):
    """This form is used to view and edit a particular User's info via the My Profile link.
    """
    id = HiddenField('User_Id')


class UserForm(SignupForm):
    """This form is used to view and edit a particular User record in the ELIXIR DCP database.
    It is intended that the admin updates user roles using this form.
    """
    id = HiddenField('User_Id')
    assigned_role_ids = SelectMultipleField('Has Roles', coerce=int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assigned_role_ids.choices = [(rol.id, rol.name) for rol in Role.query.all()]


__all__ = [SubmissionForm, ContactForm, AttachmentForm, DatadecForm, UserForm, MyProfileForm, MessageForm]
