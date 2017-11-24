# coding=utf-8
import enum
from elixir_dcp import db
from flask_login import UserMixin
from . import submission

__author__ = 'Valentin Grouès'

# many to many intermediate tables
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

from elixir_dcp.models.role import Role
from elixir_dcp.models.submission import Submission
from elixir_dcp.models.user import User

__all__ = [Submission, User, Role, roles_users]

class UserRoleEnum(enum.Enum):
    steward = '1'
    user = '2'
    # TODO can there be other roles?


class ElixirDcpUser(db.Model, UserMixin):
    __tablename__ = 'elixir_dcp_users'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)     # ['Mr', 'Ms', 'Prof', 'Dr']
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    elixir_reg_id = db.Column(db.String, unique=True)
    phone_code = db.Column(db.String)
    phone_no = db.Column(db.String)
    usr_role = db.Column(db.Enum(UserRoleEnum), default=UserRoleEnum.user, nullable=False)


__all__ = [submission, ElixirDcpUser, UserRoleEnum]




