# coding=utf-8
from flask import flash, redirect, render_template, request, url_for

import elixir_dcp.forms as forms
import elixir_dcp.models as models
import sys

from dateutil import parser

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


@app.route('/submissions/<int:sub_id>/edit', methods=['GET', 'POST'])
def add_edit_submission(sub_id):

    if request.method == 'GET':
        form = forms.SubmissionForm()
        if sub_id == 0:
            form.id.data = sub_id
            # An empty form to create a submission a new
        else:

            submission_rec = models.Submission.query.get_or_404(sub_id)

            # a form filled in with info from the db  record that shall be edited
            # form.populate did not work TODO ask Valentin
            form.id.data = submission_rec.id
            form.name.data = submission_rec.name
            form.description.data = submission_rec.description
            form.created.data = submission_rec.created
        return render_template('submission/editor.html', form=form)

    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        if form.validate_on_submit():
            if int(form.id.data) == 0:
                submission_rec = models.Submission()
                submission_rec.name = form.name.data
                submission_rec.description = form.description.data
                submission_rec.created = form.created.data
                db.session.add(submission_rec)
                db.session.add(submission_rec)
                db.session.commit()
                flash('Submission created successfully', 'info')
            else:
                submission_rec = models.Submission.query.filter_by(id=form.id.data).first()
                submission_rec.name = form.name.data
                submission_rec.description = form.description.data
                submission_rec.created = form.created.data
                db.session.add(submission_rec)
                db.session.commit()
                flash('Submission updated successfully', 'info')

            return redirect(url_for('list_submissions'))
        else:
            print(form.errors, file=sys.stderr)
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/editor.html', form=form)


