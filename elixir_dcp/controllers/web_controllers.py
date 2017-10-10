# coding=utf-8
from flask import render_template

from elixir_dcp import app

__author__ = 'Valentin Grouès'


@app.route('/', methods=['GET'])
def datasets():
    return render_template('home.html')
