# coding=utf-8
from elixir_dcp.forms.submissions_forms import AttachmentForm, ContactForm, SubmissionAccessForm, SubmissionForm, \
    StudyDishForm, UseConditionGroupForm, UploadInfoForm
from wtforms import HiddenField,StringField
from wtforms.fields.html5 import EmailField
from flask_wtf import FlaskForm #, RecaptchaField
from flask import redirect, request
from urllib.parse import urlparse, urljoin
from wtforms.validators import Email, DataRequired, Length, Regexp

__author__ = 'Valentin Grouès'


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


class SignupForm(FlaskForm):
    elixir_sub_id = HiddenField('Elixir Sub ID')
    first_name = StringField('First Name', [DataRequired(), Regexp('\w+', message="Names can contain only letters numbers or underscore"), Length(min=2, max=20, message="First name must be between 2 & 20 characters")])
    last_name = StringField('Last Name', [DataRequired(), Regexp('\w+', message="Names can contain only letters numbers or underscore"), Length(min=2, max=20, message="Last name must be between 2 & 20 characters")])
    email = EmailField('E-Mail', [DataRequired()],
                       render_kw={"placeholder": "Email address that ELIXIR LU should contact you."})
    #recaptcha = RecaptchaField()

__all__ = [SubmissionForm, ContactForm, AttachmentForm, StudyDishForm, UseConditionGroupForm, SubmissionAccessForm]






