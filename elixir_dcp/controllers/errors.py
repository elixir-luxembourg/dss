# coding=utf-8
__author__ = 'Valentin Grouès'

from flask import render_template
from flask_wtf.csrf import CSRFError

from elixir_dcp import app


@app.errorhandler(CSRFError)
def csrf_error(reason):
    explanation = "The session might have timed out, try to go back and refresh the page before doing any action"
    return render_template('error.html', message="Error 400 - " + reason,
                           explanation=explanation), 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Error 404 - Page not found", show_home_link=True), 404
