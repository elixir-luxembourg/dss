__author__ = "Valentin Grouès"


class ElixirDCPException(Exception):
    pass


class AuthenticationException(ElixirDCPException):
    pass


class RecordNotExistsException(ElixirDCPException):
    pass


class RecordLifecycleException(ElixirDCPException):
    pass
