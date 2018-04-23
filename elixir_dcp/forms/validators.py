import re
from wtforms.validators import ValidationError

class OptionalFieldValidator(object):

    def __init__(self, message=None, regex_str=None):
        self.message = message
        self.regex_str = regex_str

    def __call__(self, form, field):
        match =True
        if field.data:
            prog = re.compile(self.regex_str)
            match = prog.match(field.data)
        if not match:
            raise ValidationError(self.message)
        return match