# coding=utf-8
from elixir_dcp.forms.submissions_forms import AttachmentForm, ContactForm, SubmissionForm, \
    StudyDishForm, UploadInfoForm
from elixir_dcp.models.security import Role
from wtforms import BooleanField, HiddenField, StringField, PasswordField, SelectMultipleField
from wtforms.fields.html5 import EmailField
from flask_wtf import FlaskForm
from flask import redirect, request
from urllib.parse import urlparse, urljoin
from wtforms.validators import Email, DataRequired, Length, Regexp

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


def check_phone(form, field):
    """Form validation: fails if the phone field is not recognisable by the google phonenumber library."""
    # w = form.w.data
    # T = field.data
    # period = 2*pi/w
    # if T > 30*period:
    #     num_periods = int(round(T/period))
    #     raise validators.ValidationError(
    #         'Cannot plot as much as %d periods! T<%.2f' %
    #         (num_periods, 30*period))


class LoginForm(RedirectForm):
    username = EmailField('Username', [DataRequired(), Email("This field requires a valid email address")],
                          render_kw={"placeholder": "email@uni.lux"})
    password = PasswordField('Password', [DataRequired()],
                             render_kw={"placeholder": "UL password"})
    remember = BooleanField('Remember me')


class SignupForm(FlaskForm):
    elixir_sub_id = HiddenField('Elixir Sub ID')
    first_name = StringField('First Name', [DataRequired(),
                                            Regexp('\w+', message="Names can contain letters, numbers or underscore."),
                                            Length(min=2, max=20, message="Must be between 2 & 20 characters.")])
    last_name = StringField('Last Name',
                            [DataRequired(), Regexp('\w+', message="Names can contain letters, numbers or underscore."),
                             Length(min=2, max=20, message="Must be between 2 & 20 characters.")])
    institution = StringField('Institution', [DataRequired()])
    email = EmailField('E-Mail', [DataRequired(), Email("This field requires an email address.")],
                       render_kw={"placeholder": "Email with which ELIXIR-LU can contact you."})

    addr_line1 = StringField('Address', render_kw={"placeholder": "Street Address."})
    addr_line2 = StringField('City', render_kw={"placeholder": "City, Country, Postal Code."})

    phone_no = StringField('Phone', [check_phone])


class UserForm(SignupForm):

    id = HiddenField('User_Id')
    assigned_role_ids = SelectMultipleField('Has Roles', coerce=int)

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.assigned_role_ids.choices = [(rol.id, rol.name) for rol in Role.query.all()]


__all__ = [SubmissionForm, ContactForm, AttachmentForm, StudyDishForm, UserForm]
