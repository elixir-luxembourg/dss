# coding=utf-8
from elixir_dcp.forms.submissions_forms import SubmissionForm, ContactForm, AttachmentForm
from wtforms import PasswordField, HiddenField, BooleanField
from wtforms.fields.html5 import EmailField
from flask_wtf import FlaskForm
from flask import redirect, request
from urllib.parse import urlparse, urljoin
from wtforms.validators import Email, DataRequired

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

class LoginForm(RedirectForm):
    elixir_reg_id = EmailField('Username', [DataRequired(), Email("This field requires the email address which is your ELIXIR AAI identity.")],
                          render_kw={"placeholder": "email@uni.lu"})
    password = PasswordField('Password', [DataRequired()],
                             render_kw={"placeholder": "Password"})
    remember = BooleanField('Remember me')

__all__ = [SubmissionForm, ContactForm, AttachmentForm, LoginForm]






