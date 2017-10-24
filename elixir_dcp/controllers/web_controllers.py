# coding=utf-8
from flask import render_template

import elixir_dcp.forms as forms
import elixir_dcp.models as models
from elixir_dcp import app

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


@app.route('/submissions/add', methods=['GET', 'POST'])
def add_submission():
    """
   Add a submission to the database
   """

    form = forms.SubmissionForm()
    return render_template('submission/editor.html',
                           form=form, title="Create new submission")
