# coding=utf-8
from flask_security import RoleMixin

from elixir_dcp import db

__author__ = 'Valentin Grouès'


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
