from abc import ABC, abstractmethod
from time import time


class LoxCallable(ABC):
    @abstractmethod
    def arity(self):
        pass

    @abstractmethod
    def call(self, interpreter, arguments):
        pass


class Clock(LoxCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return time()

    def __str__(self):
        return "<native fn>"


class Read(LoxCallable):
    def arity(self):
        return 1

    def call(self, interpreter, arguments):
        return input(arguments[0])

    def __str__(self):
        return "<native fn>"


class Float(LoxCallable):
    def arity(self):
        return 1

    def call(self, interpreter, arguments):
        try:
            return float(arguments[0])
        except ValueError:
            return None

    def __str__(self):
        return "<native fn>"
