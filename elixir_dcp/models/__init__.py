# coding=utf-8
from elixir_dcp import db

__author__ = 'Valentin Grouès'

# many to many intermediate tables
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

from elixir_dcp.models.role import Role
from elixir_dcp.models.submission import Submission
from elixir_dcp.models.user import User

__all__ = [Submission, User, Role, roles_users]
