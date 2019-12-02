from Lox.LoxCallable import LoxCallable
from Lox.LoxInstance import LoxInstance


class LoxClass(LoxCallable):
    def __init__(self, name, superclass, methods):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def find_method(self, name):
        if self.methods.keys().__contains__(name):
            return self.methods[name]
        elif self.superclass is not None:
            return self.superclass.find_method(name)
        else:
            return None

    def __str__(self):
        return self.name

    def call(self, interpreter, arguments):
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def arity(self):
        initializer = self.find_method("init")
        if initializer is None:
            return 0
        else:
            return initializer.arity()
