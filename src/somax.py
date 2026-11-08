
import re
import sys
import ast
from pathlib import Path


TOKEN_PATTERN = re.compile(
    r'(?P<WS>\s+)'
    r'|(?P<COMMENT>##[^\n]*)'
    r'|(?P<FSTRING>f"(?:\\.|[^"\\])*")'
    r'|(?P<STRING>"(?:\\.|[^"\\])*")'
    r'|(?P<NUMBER>\d+(?:\.\d+)?)'
    r'|(?P<IDENT>[A-Za-z_]\w*)'
    r'|(?P<OP>\+\+|--|==|!=|<=|>=|\*\*|[+\-*/%<>=(),;.{}])'
)


class SomaxError(Exception):
    pass


class ReturnSignal(Exception):

    def __init__(self, value):
        self.value = value


class Interpreter:

    TYPES = ("int", "float", "string", "bool")

    PRECEDENCE = {
        "or": 1,
        "and": 2,
        "==": 3,
        "!=": 3,
        "<": 4,
        ">": 4,
        "<=": 4,
        ">=": 4,
        "+": 5,
        "-": 5,
        "*": 6,
        "/": 6,
        "%": 6,
        "**": 7
    }

    def __init__(self, source):
        self.tokens = self.tokenize(source)
        self.position = 0
        self.scopes = [{}]
        self.scope_types = [{}]
        self.functions = {}
        self.call_depth = 0

    def tokenize(self, source):
        tokens = []
        position = 0
        line = 1
        column = 1

        while position < len(source):
            match = TOKEN_PATTERN.match(source, position)

            if not match:
                raise SomaxError(
                    f"Unexpected character '{source[position]}' "
                    f"at line {line}, column {column}"
                )

            kind = match.lastgroup
            value = match.group()

            if kind not in ("WS", "COMMENT"):
                tokens.append((kind, value, line, column))

            lines = value.split("\n")

            if len(lines) > 1:
                line += len(lines) - 1
                column = len(lines[-1]) + 1
            else:
                column += len(value)

            position = match.end()

        tokens.append(("EOF", "", line, column))
        return tokens

    def current(self):
        return self.tokens[self.position]

    def advance(self):
        token = self.current()

        if token[0] != "EOF":
            self.position += 1

        return token

    def error(self, message, token=None):
        token = token or self.current()
        _, _, line, column = token

        raise SomaxError(
            f"{message} at line {line}, column {column}"
        )

    def expect(self, value):
        if self.current()[1] != value:
            self.error(
                f"Expected '{value}', got '{self.current()[1]}'"
            )

        return self.advance()

    def parse(self):
        while self.current()[0] != "EOF":
            self.statement()

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None

    def lookup_type(self, name):
        for scope in reversed(self.scope_types):
            if name in scope:
                return scope[name]

        return None

    def declare(self, name, data_type, value, token):
        if name in self.scopes[-1]:
            self.error(f"Variable '{name}' already exists", token)

        value = self.check_type(data_type, value, token)
        self.scopes[-1][name] = value
        self.scope_types[-1][name] = data_type

    def assign(self, name, value, token):
        for index in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[index]:
                data_type = self.scope_types[index][name]
                value = self.check_type(data_type, value, token)
                self.scopes[index][name] = value
                return

        self.error(f"Undefined variable '{name}'", token)

    def statement(self):
        kind, value, _, _ = self.current()

        if kind == "IDENT" and value in self.TYPES:
            self.declaration()
        elif value == "out":
            self.output()
        elif value == "if":
            self.if_statement()
        elif value == "while":
            self.while_statement()
        elif value == "for":
            self.for_statement()
        elif value == "function":
            self.function_declaration()
        elif value == "return":
            self.return_statement()
        elif value == "}":
            self.error("Unexpected closing brace")
        elif kind == "IDENT":
            self.assignment_or_call()
        else:
            self.error(f"Unexpected statement '{value}'")

    def block(self):
        self.expect("{")

        while self.current()[1] != "}":
            if self.current()[0] == "EOF":
                self.error("Unclosed block")

            self.statement()

        self.expect("}")

    def declaration(self, semicolon=True):
        data_type = self.advance()[1]
        name_token = self.advance()
        name = name_token[1]

        if name_token[0] != "IDENT":
            self.error("Expected a variable name", name_token)

        self.expect("=")
        value = self.expression()

        if semicolon:
            self.expect(";")

        self.declare(name, data_type, value, name_token)

    def assignment_or_call(self, semicolon=True):
        name_token = self.current()

        if self.position + 1 < len(self.tokens):
            next_value = self.tokens[self.position + 1][1]

            if next_value == "(":
                self.expression()
                if semicolon:
                    self.expect(";")
                return

            if next_value in ("++", "--"):
                self.advance()
                operator = self.advance()[1]

                current = self.lookup(name_token[1])

                if current is None:
                    self.error(f"Undefined variable '{name_token[1]}'", name_token)

                if type(current) not in (int, float):
                    self.error("Increment and decrement require numbers", name_token)

                self.assign(
                    name_token[1],
                    current + (1 if operator == "++" else -1),
                    name_token
                )

                if semicolon:
                    self.expect(";")

                return

        name = self.advance()[1]

        if self.lookup(name) is None:
            self.error(f"Undefined variable '{name}'", name_token)

        self.expect("=")
        value = self.expression()

        if semicolon:
            self.expect(";")

        self.assign(name, value, name_token)

    def output(self):
        self.expect("out")
        self.expect(".")
        self.expect("print")
        self.expect("(")

        value = self.expression()

        self.expect(")")
        self.expect(";")

        if type(value) is bool:
            value = str(value).lower()

        print(value)

    def check_type(self, data_type, value, token):
        actual_type = type(value)

        valid = {
            "int": actual_type is int,
            "float": actual_type in (int, float),
            "string": actual_type is str,
            "bool": actual_type is bool
        }

        if not valid[data_type]:
            self.error(
                f"Type mismatch: expected {data_type}, "
                f"got {actual_type.__name__}",
                token
            )

        if data_type == "float":
            return float(value)

        return value

    def if_statement(self):
        self.expect("if")
        condition = self.expression()

        if type(condition) is not bool:
            self.error("If condition must evaluate to bool")

        self.expect("then")

        if condition:
            self.body()
            if self.current()[1] == "else":
                self.advance()
                if self.current()[1] == "if":
                    self.skip_statement()
                else:
                    self.skip_body()
        else:
            self.skip_body()

            if self.current()[1] == "else":
                self.advance()

                if self.current()[1] == "if":
                    self.if_statement()
                else:
                    self.body()

    def body(self):
        if self.current()[1] == "{":
            self.block()
        else:
            self.statement()

    def skip_statement(self):
        if self.current()[1] == "{":
            self.skip_body()
        else:
            depth = 0

            while self.current()[0] != "EOF":
                value = self.advance()[1]

                if value == "(":
                    depth += 1
                elif value == ")":
                    depth -= 1
                elif value == ";" and depth == 0:
                    break

    def skip_body(self):
        if self.current()[1] != "{":
            self.skip_statement()
            return

        depth = 0

        while self.current()[0] != "EOF":
            value = self.advance()[1]

            if value == "{":
                depth += 1
            elif value == "}":
                depth -= 1

                if depth == 0:
                    return

        self.error("Unclosed block")

    def capture_body(self):
        if self.current()[1] == "{":
            self.advance()
            depth = 1
            body = []

            while depth > 0:
                token = self.advance()

                if token[0] == "EOF":
                    self.error("Unclosed block", token)

                if token[1] == "{":
                    depth += 1
                elif token[1] == "}":
                    depth -= 1

                    if depth == 0:
                        break

                body.append(token)

            return body

        body = []
        depth = 0

        while self.current()[0] != "EOF":
            token = self.advance()
            body.append(token)

            if token[1] == "(":
                depth += 1
            elif token[1] == ")":
                depth -= 1
            elif token[1] == ";" and depth == 0:
                break

        if not body or body[-1][1] != ";":
            self.error("Expected a statement ending with ';'")

        return body

    def evaluate_tokens(self, tokens):
        saved_tokens = self.tokens
        saved_position = self.position

        self.tokens = tokens + [("EOF", "", 0, 0)]
        self.position = 0

        try:
            result = self.expression()

            if self.current()[0] != "EOF":
                self.error("Unexpected token in expression")

            return result

        finally:
            self.tokens = saved_tokens
            self.position = saved_position

    def execute_tokens(self, tokens):
        saved_tokens = self.tokens
        saved_position = self.position

        self.tokens = tokens + [("EOF", "", 0, 0)]
        self.position = 0

        try:
            self.parse()
        finally:
            self.tokens = saved_tokens
            self.position = saved_position

    def while_statement(self):
        self.expect("while")

        start = self.position
        condition = self.expression()
        condition_tokens = self.tokens[start:self.position]

        self.expect("then")
        body = self.capture_body()

        if type(condition) is not bool:
            self.error("While condition must evaluate to bool")

        while self.evaluate_tokens(condition_tokens):
            self.execute_tokens(body)

    def for_statement(self):
        self.expect("for")
        self.expect("(")

        self.scopes.append({})
        self.scope_types.append({})

        try:
            if self.current()[1] in self.TYPES:
                self.declaration()
            else:
                self.assignment_or_call()

            condition_start = self.position
            self.expression()
            condition_tokens = self.tokens[condition_start:self.position]

            self.expect(";")

            update = []

            while self.current()[1] != ")":
                if self.current()[0] == "EOF":
                    self.error("Expected ')' in for loop")

                update.append(self.advance())

            self.expect(")")
            self.expect("then")

            body = self.capture_body()

            while self.evaluate_tokens(condition_tokens):
                self.execute_tokens(body)
                self.execute_tokens(update + [("OP", ";", 0, 0)])

        finally:
            self.scopes.pop()
            self.scope_types.pop()

    def function_declaration(self):
        self.expect("function")

        name_token = self.advance()
        name = name_token[1]

        if name_token[0] != "IDENT":
            self.error("Expected function name", name_token)

        if name in self.functions:
            self.error(f"Function '{name}' already exists", name_token)

        self.expect("(")

        parameters = []

        while self.current()[1] != ")":
            data_type = self.advance()[1]

            if data_type not in self.TYPES:
                self.error("Expected parameter type")

            parameter = self.advance()

            if parameter[0] != "IDENT":
                self.error("Expected parameter name", parameter)

            if any(p[1] == parameter[1] for p in parameters):
                self.error(f"Duplicate parameter '{parameter[1]}'", parameter)

            parameters.append((data_type, parameter[1]))

            if self.current()[1] != ",":
                break

            self.advance()

        self.expect(")")
        body = self.capture_body()

        self.functions[name] = (parameters, body)

    def return_statement(self):
        token = self.expect("return")

        if self.call_depth == 0:
            self.error("Return outside a function", token)

        value = None

        if self.current()[1] != ";":
            value = self.expression()

        self.expect(";")
        raise ReturnSignal(value)

    def call_function(self, name, arguments, token):
        if name not in self.functions:
            self.error(f"Undefined function '{name}'", token)

        parameters, body = self.functions[name]

        if len(arguments) != len(parameters):
            self.error(
                f"Function '{name}' expects {len(parameters)} "
                f"arguments, got {len(arguments)}",
                token
            )

        if self.call_depth >= 100:
            self.error("Maximum function call depth exceeded", token)

        self.scopes.append({})
        self.scope_types.append({})
        self.call_depth += 1

        try:
            for (data_type, parameter), value in zip(parameters, arguments):
                self.declare(parameter, data_type, value, token)

            try:
                self.execute_tokens(body)
            except ReturnSignal as result:
                return result.value

            return None

        finally:
            self.call_depth -= 1
            self.scopes.pop()
            self.scope_types.pop()

    def expression(self, min_precedence=0):
        left = self.primary()

        while True:
            operator = self.current()[1]
            precedence = self.PRECEDENCE.get(operator, -1)

            if precedence < min_precedence:
                break

            token = self.advance()
            next_precedence = (
                precedence if operator == "**"
                else precedence + 1
            )

            right = self.expression(next_precedence)
            left = self.apply(operator, left, right, token)

        return left

    def primary(self):
        token = self.advance()
        kind, value, _, _ = token

        if kind == "NUMBER":
            return float(value) if "." in value else int(value)

        if kind == "STRING":
            return ast.literal_eval(value)

        if kind == "FSTRING":
            text = ast.literal_eval(value[1:])

            def replace(match):
                name = match.group(1)
                result = self.lookup(name)

                if result is None:
                    self.error(f"Undefined variable '{name}'", token)

                return str(result)

            return re.sub(r"\{([A-Za-z_]\w*)\}", replace, text)

        if kind == "IDENT":
            if value == "true":
                return True

            if value == "false":
                return False

            if self.current()[1] == "(":
                self.advance()
                arguments = []

                while self.current()[1] != ")":
                    arguments.append(self.expression())

                    if self.current()[1] != ",":
                        break

                    self.advance()

                self.expect(")")
                return self.call_function(value, arguments, token)

            result = self.lookup(value)

            if result is None:
                self.error(f"Undefined variable '{value}'", token)

            return result

        if value == "(":
            result = self.expression()
            self.expect(")")
            return result

        if value in ("+", "-"):
            operand = self.primary()

            if type(operand) not in (int, float):
                self.error("Unary operators require numbers", token)

            return operand if value == "+" else -operand

        self.error(f"Unexpected expression '{value}'", token)

    def apply(self, operator, left, right, token):
        if operator in ("and", "or"):
            if type(left) is not bool or type(right) is not bool:
                self.error(f"Operator '{operator}' requires boolean values", token)

        if operator in ("<", ">", "<=", ">="):
            if type(left) not in (int, float) or type(right) not in (int, float):
                self.error("Comparison requires numeric values", token)

        operations = {
            "+": lambda: left + right,
            "-": lambda: left - right,
            "*": lambda: left * right,
            "/": lambda: left / right,
            "%": lambda: left % right,
            "**": lambda: left ** right,
            "==": lambda: left == right,
            "!=": lambda: left != right,
            "<": lambda: left < right,
            ">": lambda: left > right,
            "<=": lambda: left <= right,
            ">=": lambda: left >= right,
            "and": lambda: left and right,
            "or": lambda: left or right
        }

        try:
            return operations[operator]()
        except (TypeError, ZeroDivisionError, OverflowError) as error:
            self.error(str(error), token)


def run_file(filename):
    try:
        source = Path(filename).read_text(encoding="utf-8")
        Interpreter(source).parse()

    except SomaxError as error:
        print(f"Somax Error: {error}")
        sys.exit(1)

    except OSError as error:
        print(f"File Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python somax.py <file.smx>")
        sys.exit(1)

    run_file(sys.argv[1])
