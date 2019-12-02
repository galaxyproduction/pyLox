from Lox.LoxCallable import LoxCallable
from Lox import Enviorment
from LoxErrors.ReturnException import Return


class LoxFunction(LoxCallable):
    def __init__(self, declaration, closure, is_init):
        self.declaration = declaration
        self.closure = closure
        self.isInit = is_init

    def bind(self, instance):
        environment = Enviorment.Environment(self.closure)
        environment.define("this", instance)
        return LoxFunction(self.declaration, environment, self.isInit)

    def call(self, interpreter, arguments):
        environment = Enviorment.Environment(self.closure)

        for i in range(len(self.declaration.params)):
            environment.define(self.declaration.params[i].lexem, arguments[i])

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except Return as return_value:
            return return_value.value

        if self.isInit:
            return self.closure.get_at(0, "this")

        return None

    def arity(self):
        return len(self.declaration.params)

    def __str__(self):
        return f"<fn {self.declaration.name.lexem}>"
