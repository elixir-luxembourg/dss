# coding=utf-8
import calendar

from flask import flash, redirect, render_template, request, url_for, g

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


@app.route('/submissions/edit/<int:sub_id>', methods=['GET', 'POST'])
def add_edit_submission(sub_id):
    """
    I used the id -> 0 to differentiate between CREATE and EDIT mode
    """
    # TODO: Find a more elegant way to determine page mode both for templates and controllers

    if request.method == 'GET':

        if sub_id == 0:
            #  an empty form
            empty_sub_form = forms.SubmissionForm()
            return render_template('submission/editor.html', submsn_form=empty_sub_form)

        else:
            #  a form filled  with info from the db
            submission_rec = models.Submission.query.get_or_404(sub_id)
            sub_form = forms.SubmissionForm(obj=submission_rec)

        return render_template('submission/editor.html', submsn_form=sub_form)

    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        if form.validate_on_submit():
            if int(form.id.data) == 0:
                submission_rec = models.Submission()

                # We do not call form.populate_obj in this case because it sets the
                # id to 0 and this gets persisted. If id is not set SQLAlchemy auto assigns.
                # TODO: its ugly, fix it

                submission_rec.created = form.created.data
                submission_rec.name = form.name.data
                submission_rec.description = form.description.data

                db.session.add(submission_rec)
                db.session.commit()
                flash('Submission created successfully', 'info')
            else:
                submission_rec = models.Submission.query.filter_by(id=form.id.data).first()
                form.populate_obj(submission_rec)
                db.session.add(submission_rec)
                db.session.commit()
                flash('Submission updated successfully', 'info')

            return redirect(url_for('list_submissions'))
        else:
            print(form.errors, file=sys.stderr)
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/editor.html', form=form)


@app.route('/submission_contact', methods=['POST'])
def add_submission_contact():
    form = forms.ContactForm(request.form)
    if form.validate_on_submit():
        contact = models.SubmissionContact()
        contact.name = form.name.data
        contact.is_primary = form.is_primary.data
        contact.submission_id = form.submission_id.data
        db.session.add(contact)
        db.session.commit()
        flash("Submission Contact added", "info")
        return "", 204
    else:
        flash("Please check the validity of your input in highlighted places", "error")
        return "", 400


@app.route('/submission_contact/<int:sub_contact_id>', methods=['DELETE'])
def delete_submission_contact(sub_contact_id):
    submission_contact = models.SubmissionContact.query.get_or_404(sub_contact_id)
    db.session.delete(submission_contact)
    db.session.commit()
    flash("Submission Contact deleted", "info")
    return "", 204


@app.route('/submission_contacts/<int:sub_id>', methods=['GET'])
def list_submission_contacts(sub_id):
    if sub_id == 0:
        contacts = None

    else:
        contacts = models.SubmissionContact.query.filter_by(submission_id=sub_id)
    contct_form = forms.ContactForm()
    contct_form.submission_id.data = sub_id
    return render_template('submission/contactsInline.html', contacts=contacts, contct_form=contct_form)
