from .errors import RuntimeErrorSomax

class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.types = {}
        self.parent = parent

    def define(self, name, value, type_name=None):
        if name in self.values:
            raise RuntimeErrorSomax(f"'{name}' is already declared")
        self.values[name] = value
        if type_name:
            self.types[name] = type_name

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeErrorSomax(f"Undefined name '{name}'")

    def get_type(self, name):
        if name in self.types:
            return self.types[name]
        if self.parent:
            return self.parent.get_type(name)
        return None

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise RuntimeErrorSomax(f"Undefined name '{name}'")
