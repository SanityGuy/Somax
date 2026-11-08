import re
from pathlib import Path
from .environment import Environment
from .errors import RuntimeErrorSomax
from .semantic import validate
from .modules import native_modules, NativeModule

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class SomaxFunction:
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure

    def call(self, runtime, arguments):
        params = self.declaration.params
        if len(arguments) != len(params):
            raise RuntimeErrorSomax(f"{self.declaration.name}() expects {len(params)} argument(s), got {len(arguments)}")
        local = Environment(self.closure)
        for (type_name, name, line, column), value in zip(params, arguments):
            local.define(name, validate(type_name, value, name), type_name)
        try:
            runtime.execute_block(self.declaration.body.statements, local)
        except ReturnSignal as signal:
            return signal.value
        return None

class SomaxArray(list):
    pass

class Runtime:
    def __init__(self, filename=None, base_dir=None):
        self.filename = filename
        self.base_dir = Path(base_dir or (Path(filename).resolve().parent if filename else Path.cwd()))
        self.globals = Environment()
        self.environment = self.globals
        self.modules = native_modules(self)
        self.loading = set()
        self.output = []
        self.globals.define("out", NativeModule("out", {
            "print": self.output_print,
            "println": self.output_print
        }))

    def output_print(self, *values):
        line = " ".join(self.stringify(v) for v in values)
        print(line)
        self.output.append(line)
        return None

    def stringify(self, value):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            return ", ".join(self.stringify(v) for v in value)
        return str(value)

    def run(self, statements):
        self.execute_block(statements, self.globals)

    def execute_block(self, statements, environment):
        previous = self.environment
        self.environment = environment
        try:
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def execute(self, node):
        from . import ast_nodes as a
        if isinstance(node, a.Block):
            self.execute_block(node.statements, Environment(self.environment))
        elif isinstance(node, a.VarDecl):
            value = self.evaluate(node.initializer) if node.initializer else self.default_value(node.type_name)
            value = validate(node.type_name, value, node.name)
            self.environment.define(node.name, value, node.type_name)
        elif isinstance(node, a.FunctionDecl):
            self.environment.define(node.name, SomaxFunction(node, self.environment))
        elif isinstance(node, a.ImportDecl):
            self.import_module(node.name, node.alias, node.line, node.column)
        elif isinstance(node, a.ExprStmt):
            self.evaluate(node.expression)
        elif isinstance(node, a.IfStmt):
            if self.truthy(self.evaluate(node.condition)):
                self.execute(node.then_branch)
            elif node.else_branch:
                self.execute(node.else_branch)
        elif isinstance(node, a.WhileStmt):
            count = 0
            while self.truthy(self.evaluate(node.condition)):
                self.execute(node.body)
                count += 1
                if count > 1000000:
                    raise RuntimeErrorSomax("Loop iteration limit exceeded")
        elif isinstance(node, a.ForStmt):
            scope = Environment(self.environment)
            previous = self.environment
            self.environment = scope
            try:
                if node.initializer:
                    self.execute(node.initializer)
                count = 0
                while node.condition is None or self.truthy(self.evaluate(node.condition)):
                    self.execute(node.body)
                    if node.update:
                        self.evaluate(node.update)
                    count += 1
                    if count > 1000000:
                        raise RuntimeErrorSomax("Loop iteration limit exceeded")
            finally:
                self.environment = previous
        elif isinstance(node, a.ReturnStmt):
            raise ReturnSignal(self.evaluate(node.value) if node.value else None)
        else:
            raise RuntimeErrorSomax(f"Unsupported statement {type(node).__name__}")

    def default_value(self, type_name):
        defaults = {"int": 0, "INT": 0, "float": 0.0, "FLOAT": 0.0, "double": 0.0, "DOUBLE": 0.0,
                    "string": "", "STRING": "", "char": "\0", "CHAR": "\0", "bool": False, "BOOL": False,
                    "bit": 0, "BIT": 0, "array": [], "ARRAY": []}
        return defaults[type_name]

    def evaluate(self, node):
        from . import ast_nodes as a
        if node is None:
            return None
        if isinstance(node, a.Literal):
            if isinstance(node.value, tuple) and node.value[0] == "FSTRING":
                return self.interpolate(node.value[1])
            return node.value
        if isinstance(node, a.Variable):
            return self.environment.get(node.name)
        if isinstance(node, a.ArrayLiteral):
            return SomaxArray(self.evaluate(x) for x in node.elements)
        if isinstance(node, a.Unary):
            value = self.evaluate(node.right)
            if node.operator == "-":
                return -value
            if node.operator == "not":
                return not self.truthy(value)
        if isinstance(node, a.Binary):
            left = self.evaluate(node.left)
            if node.operator == "and":
                return self.truthy(left) and self.truthy(self.evaluate(node.right))
            if node.operator == "or":
                return self.truthy(left) or self.truthy(self.evaluate(node.right))
            right = self.evaluate(node.right)
            return self.binary(left, node.operator, right)
        if isinstance(node, a.Assign):
            value = self.evaluate(node.value)
            self.assign_target(node.target, value)
            return value
        if isinstance(node, a.Get):
            obj = self.evaluate(node.object)
            return self.get_member(obj, node.name)
        if isinstance(node, a.Index):
            obj = self.evaluate(node.object)
            index = self.evaluate(node.index)
            try:
                if not isinstance(index, int):
                    raise RuntimeErrorSomax("Array index must be an integer")
                return obj[index]
            except (IndexError, TypeError):
                raise RuntimeErrorSomax(f"Index {index} is out of range or value is not indexable")
        if isinstance(node, a.Call):
            callee = self.evaluate(node.callee)
            args = [self.evaluate(x) for x in node.arguments]
            if isinstance(callee, SomaxFunction):
                return callee.call(self, args)
            if callable(callee):
                try:
                    return callee(*args)
                except RuntimeErrorSomax:
                    raise
                except Exception as exc:
                    raise RuntimeErrorSomax(str(exc))
            raise RuntimeErrorSomax("This value cannot be called")
        raise RuntimeErrorSomax(f"Unsupported expression {type(node).__name__}")

    def binary(self, left, op, right):
        try:
            if op == "+": return left + right
            if op == "-": return left - right
            if op == "*": return left * right
            if op == "/": return left / right
            if op == "%": return left % right
            if op == "==": return left == right
            if op == "!=": return left != right
            if op == ">": return left > right
            if op == ">=": return left >= right
            if op == "<": return left < right
            if op == "<=": return left <= right
        except Exception as exc:
            raise RuntimeErrorSomax(str(exc))
        raise RuntimeErrorSomax(f"Unknown operator '{op}'")

    def truthy(self, value):
        return bool(value)

    def assign_target(self, target, value):
        from . import ast_nodes as a
        if isinstance(target, a.Variable):
            expected = self.environment.get_type(target.name)
            if expected:
                value = validate(expected, value, target.name)
            self.environment.assign(target.name, value)
            return
        if isinstance(target, a.Index):
            obj = self.evaluate(target.object)
            index = self.evaluate(target.index)
            if not isinstance(obj, list) or not isinstance(index, int):
                raise RuntimeErrorSomax("Indexed assignment requires an array and integer index")
            try:
                obj[index] = value
            except IndexError:
                raise RuntimeErrorSomax(f"Index {index} is out of range")
            return
        if isinstance(target, a.Get):
            obj = self.evaluate(target.object)
            if isinstance(obj, NativeModule):
                raise RuntimeErrorSomax("Cannot assign to a module member")
            raise RuntimeErrorSomax("This property cannot be assigned")

    def get_member(self, obj, name):
        if isinstance(obj, NativeModule):
            return obj.get(name)
        if isinstance(obj, list):
            methods = {
                "length": lambda: len(obj),
                "findExact": lambda value: next((i for i, item in enumerate(obj) if item == value), -1),
                "add": lambda value: obj.append(value),
                "remove": lambda value: self.array_remove(obj, value),
                "deserialize": lambda: "".join(self.stringify(x) for x in obj),
                "space": lambda: " ".join(self.stringify(x) for x in obj)
            }
            if name in methods:
                return methods[name]
        if isinstance(obj, str):
            methods = {
                "length": lambda: len(obj),
                "upper": lambda: obj.upper(),
                "lower": lambda: obj.lower(),
                "trim": lambda: obj.strip(),
                "contains": lambda value: str(value) in obj,
                "replace": lambda old, new: obj.replace(str(old), str(new)),
                "split": lambda separator=" ": obj.split(str(separator)),
                "space": lambda: " ".join(obj)
            }
            if name in methods:
                return methods[name]
        raise RuntimeErrorSomax(f"Value has no member '{name}'")

    def array_remove(self, array, value):
        try:
            array.remove(value)
            return True
        except ValueError:
            return False

    def interpolate(self, template):
        pattern = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:\[\d+\])*)\}")
        def replace(match):
            expr = match.group(1)
            value = self.environment.get(expr.split(".")[0].split("[")[0])
            rest = expr[len(expr.split(".")[0].split("[")[0]):]
            while rest:
                if rest.startswith("."):
                    rest = rest[1:]
                    name, _, rest = rest.partition(".")
                    if "[" in name:
                        name, idx = name.split("[", 1)
                        value = self.get_member(value, name)
                        value = value(int(idx[:-1]))
                    else:
                        value = self.get_member(value, name)
                elif rest.startswith("["):
                    idx, _, rest = rest[1:].partition("]")
                    value = value[int(idx)]
                    rest = rest
                else:
                    break
            return self.stringify(value)
        return pattern.sub(replace, template)

    def import_module(self, name, alias, line, column):
        if name in self.modules:
            self.environment.define(alias, self.modules[name])
            return
        path = (self.base_dir / f"{name}.smx").resolve()
        base = self.base_dir.resolve()
        if path != base and base not in path.parents:
            raise RuntimeErrorSomax("Module path is outside the project directory", line, column, self.filename)
        if not path.is_file():
            raise RuntimeErrorSomax(f"Module '{name}' was not found", line, column, self.filename)
        if path in self.loading:
            raise RuntimeErrorSomax(f"Circular import detected for module '{name}'", line, column, self.filename)
        self.loading.add(path)
        try:
            from .lexer import Lexer
            from .parser import Parser
            source = path.read_text(encoding="utf-8")
            program = Parser(Lexer(source, str(path)).tokenize(), str(path)).parse()
            module_runtime = Runtime(str(path), path.parent)
            module_runtime.modules.update(self.modules)
            module_runtime.loading = self.loading
            module_runtime.run(program.statements)
            values = {**module_runtime.globals.values}
            self.environment.define(alias, NativeModule(name, values))
        finally:
            self.loading.remove(path)
