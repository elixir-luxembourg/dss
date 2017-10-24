# coding=utf-8
import datetime
from flask import render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask import request
from . import forms

import elixir_dcp.models as our_db_model
from elixir_dcp import app

__author__ = 'Valentin Grouès'


@app.route('/', methods=['GET'])
def datasets():
    return render_template('home.html')


@app.route('/test', methods=['GET'])
def tests():
    users = ["user1", "users2"]
    return render_template('test.html', current_date=datetime.datetime.now(), users=users)


@app.route('/submissions', methods=['GET'])
def list_submissions():
    """
    List all submissions
    """
    submissions = our_db_model.Submission.query.all()
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