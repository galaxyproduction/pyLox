from LoxErrors.RuntimeException import RuntimeException


class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name, value):
        self.values[name] = value

    def get_at(self, distance, name):
        return self.ancestor(distance).values[name]

    def ancestor(self, distance):
        environment = self
        for i in range(distance):
            environment = environment.enclosing

        return environment

    def get(self, name):
        if name.lexem in self.values.keys():
            return self.values[name.lexem]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise RuntimeException(name, f"Undefined variable '{name.lexem}'.")

    def assign_at(self, distance, name, value):
        self.ancestor(distance).values[name.lexem] = value

    def assign(self, name, value):
        if name.lexem in self.values.keys():
            self.values[name.lexem] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise RuntimeException(name, f"Undefined variable '{name.lexem}'.")
