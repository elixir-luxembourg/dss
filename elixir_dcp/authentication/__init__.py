# coding=utf-8
from abc import ABCMeta, abstractmethod

__author__ = 'Valentin Grouès'


class Authentication(metaclass=ABCMeta):
    @abstractmethod
    def authenticate_user(self, username, password):
        pass

