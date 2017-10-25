# coding=utf-8
from flask import flash, redirect, render_template, request, url_for

import elixir_dcp.forms as forms
import elixir_dcp.models as models
import sys

from elixir_dcp import app, db

__author__ = 'Valentin Grouès'


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/submissions', methods=['GET'])
def list_submissions():
    """
    List all submissions
    """
    submissions = models.Submission.query.all()
    return render_template('submission/listing.html',
                           submissions=submissions, title="Data Submissions to ELIXIR DCP")


@app.route('/submissions/<sub_id>/edit', methods=['GET', 'POST'])
def add_edit_submission(sub_id):

    form = forms.SubmissionForm()
    if sub_id == -1:

        form.id = sub_id
        # form.pi_field.choices = [(e.id, e.full_name) for e in
        #                Employee.query.filter_by(is_pi=False).order_by(Employee.first_name).all()]
    else:
        submission = models.Submission.query.get_or_404(sub_id)

        form.id = submission.id
        form.name = submission.name
        form.description = submission.description

    return render_template('submission/editor.html', form=form)
