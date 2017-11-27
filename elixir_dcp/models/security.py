from elixir_dcp import db
from flask_login._compat import text_type


class User(db.Model):
    __tablename__ = 'users'

    active_user = db.Column(db.Boolean, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)     # ['Mr', 'Ms', 'Prof', 'Dr']
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    elixir_reg_id = db.Column(db.String, unique=True)
    assigned_roles = db.relationship('Role', secondary='users_roles')
    phone_code = db.Column(db.String)
    phone_no = db.Column(db.String)

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

    def has_overlapping_role(self, role_list):
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

