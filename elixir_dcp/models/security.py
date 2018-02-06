from elixir_dcp import db
from flask_login._compat import text_type
from datetime import datetime
from elixir_dcp.exceptions import RecordNotExistsException


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    elixir_sub_id = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, unique=True)
    phone_icc = db.Column(db.String)
    phone_no = db.Column(db.String)
    assigned_roles = db.relationship('Role', secondary='users_roles')

    active_user = db.Column(db.Boolean, nullable=False)

    def is_active(self):
        return self.active_user

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return text_type(self.id)
        except AttributeError:
            raise NotImplementedError('No `id` attribute - override `get_id`')

    def has_role_from(self, role_list):
        if self.assigned_roles is None:
            return False
        else:
            role_names = []
            for role in self.assigned_roles:
                role_names.append(role.name)
        if len(set(role_list).intersection(role_names)) > 0:
            return True
        else:
            return False

    def assign_role(self, role_name):

        role = Role.query.filter_by(name=role_name).one_or_none()
        if role:
            if not self.has_role_from([role_name]):
                new_role_assignment = UsersRoles()
                new_role_assignment.user_id = self.id
                new_role_assignment.role_id = role.id
                new_role_assignment.assigned_on = datetime.now()
                db.session.add(new_role_assignment)
                db.session.commit()
        else:
            raise RecordNotExistsException("Role with specified name does not exist.")

    def is_admin(self):
        return self.has_role_from(['admin'])

    def display_name(self):
        return self.first_name + " " + self.last_name


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class UsersRoles(db.Model):
    __tablename__ = 'users_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    assigned_on = db.Column('assigned_on', db.Date())



