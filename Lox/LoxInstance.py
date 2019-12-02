from LoxErrors.RuntimeException import RuntimeException


class LoxInstance:
    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def get(self, name):
        if self.fields.keys().__contains__(name.lexem):
            return self.fields[name.lexem]

        method = self.klass.find_method(name.lexem)
        if method is not None:
            return method.bind(self)

        raise RuntimeException(name, f"Undefined property {name.lexem}.")

    def set(self, name, value):
        self.fields[name.lexem] = value

    def __str__(self):
        return self.klass.name + " <instance>"
