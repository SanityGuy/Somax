from .ast_nodes import *
from .errors import ParseError

TYPE_NAMES = {"INT", "FLOAT", "DOUBLE", "STRING", "CHAR", "BOOL", "BIT", "ARRAY"}

class Parser:
    def __init__(self, tokens, filename=None):
        self.tokens = tokens
        self.current = 0
        self.filename = filename

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def check(self, kind):
        return self.peek().kind == kind

    def advance(self):
        if not self.check("EOF"):
            self.current += 1
        return self.previous()

    def match(self, *kinds):
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def consume(self, kind, message):
        if self.check(kind):
            return self.advance()
        t = self.peek()
        raise ParseError(message, t.line, t.column, self.filename)

    def parse(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.declaration())
        t = self.peek()
        return Program(t.line, t.column, statements)

    def declaration(self):
        if self.match("IMPORT"):
            return self.import_decl()
        if self.match("FUNCTION"):
            return self.function_decl()
        if self.peek().kind in TYPE_NAMES:
            return self.var_decl(True)
        return self.statement()

    def import_decl(self):
        name = self.consume("IDENT", "Expected module name after import")
        alias = name.value
        if self.match("AS"):
            alias = self.consume("IDENT", "Expected alias after 'as'").value
        self.consume(";", "Expected ';' after import")
        return ImportDecl(name.line, name.column, name.value, alias)

    def function_decl(self):
        name = self.consume("IDENT", "Expected function name")
        self.consume("(", "Expected '(' after function name")
        params = []
        if not self.check(")"):
            while True:
                type_token = self.consume_type()
                param = self.consume("IDENT", "Expected parameter name")
                params.append((type_token.value, param.value, param.line, param.column))
                if not self.match(","):
                    break
        self.consume(")", "Expected ')' after parameters")
        body = self.block()
        return FunctionDecl(name.line, name.column, name.value, params, body)

    def consume_type(self):
        if self.peek().kind in TYPE_NAMES:
            return self.advance()
        t = self.peek()
        raise ParseError("Expected a type name", t.line, t.column, self.filename)

    def var_decl(self, semicolon):
        type_token = self.advance()
        name = self.consume("IDENT", "Expected variable name")
        initializer = None
        if self.match("="):
            initializer = self.expression()
        if semicolon:
            self.consume(";", "Expected ';' after variable declaration")
        return VarDecl(type_token.line, type_token.column, type_token.value, name.value, initializer)

    def statement(self):
        if self.match("IF"):
            return self.if_stmt()
        if self.match("WHILE"):
            return self.while_stmt()
        if self.match("FOR"):
            return self.for_stmt()
        if self.match("RETURN"):
            return self.return_stmt()
        if self.match("{"):
            return self.block_after_open(self.previous())
        expr = self.expression()
        self.consume(";", "Expected ';' after expression")
        return ExprStmt(expr.line, expr.column, expr)

    def block(self):
        token = self.consume("{", "Expected '{' before block")
        return self.block_after_open(token)

    def block_after_open(self, token):
        statements = []
        while not self.check("}") and not self.check("EOF"):
            statements.append(self.declaration())
        self.consume("}", "Expected '}' after block")
        return Block(token.line, token.column, statements)

    def body_after_then(self):
        self.consume("THEN", "Expected 'then'")
        if self.match("{"):
            return self.block_after_open(self.previous())
        return self.statement()

    def if_stmt(self):
        line, col = self.previous().line, self.previous().column
        parenthesized = self.match("(")
        condition = self.expression()
        if parenthesized:
            self.consume(")", "Expected ')' after condition")
        then_branch = self.body_after_then()
        else_branch = None
        if self.match("ELSE"):
            if self.match("IF"):
                else_branch = self.if_stmt()
            elif self.match("{"):
                else_branch = self.block_after_open(self.previous())
            else:
                else_branch = self.statement()
        return IfStmt(line, col, condition, then_branch, else_branch)

    def while_stmt(self):
        token = self.previous()
        parenthesized = self.match("(")
        condition = self.expression()
        if parenthesized:
            self.consume(")", "Expected ')' after condition")
        body = self.body_after_then()
        return WhileStmt(token.line, token.column, condition, body)

    def for_stmt(self):
        token = self.previous()
        self.consume("(", "Expected '(' after for")
        initializer = None
        if self.match(";"):
            initializer = None
        elif self.peek().kind in TYPE_NAMES:
            initializer = self.var_decl(False)
            self.consume(";", "Expected ';' after for initializer")
        else:
            e = self.expression()
            initializer = ExprStmt(e.line, e.column, e)
            self.consume(";", "Expected ';' after for initializer")
        condition = None if self.check(";") else self.expression()
        self.consume(";", "Expected ';' after for condition")
        update = None if self.check(")") else self.expression()
        self.consume(")", "Expected ')' after for clauses")
        body = self.body_after_then()
        return ForStmt(token.line, token.column, initializer, condition, update, body)

    def return_stmt(self):
        token = self.previous()
        value = None if self.check(";") else self.expression()
        self.consume(";", "Expected ';' after return")
        return ReturnStmt(token.line, token.column, value)

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.logical_or()
        if self.match("="):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, (Variable, Get, Index)):
                return Assign(equals.line, equals.column, expr, value)
            raise ParseError("Invalid assignment target", equals.line, equals.column, self.filename)
        return expr

    def logical_or(self):
        expr = self.logical_and()
        while self.match("OR"):
            op = self.previous()
            expr = Binary(op.line, op.column, expr, "or", self.logical_and())
        return expr

    def logical_and(self):
        expr = self.equality()
        while self.match("AND"):
            op = self.previous()
            expr = Binary(op.line, op.column, expr, "and", self.equality())
        return expr

    def equality(self):
        expr = self.comparison()
        while self.match("==", "!="):
            op = self.previous()
            expr = Binary(op.line, op.column, expr, op.kind, self.comparison())
        return expr

    def comparison(self):
        expr = self.term()
        while self.match(">", ">=", "<", "<="):
            op = self.previous()
            expr = Binary(op.line, op.column, expr, op.kind, self.term())
        return expr

    def term(self):
        expr = self.factor()
        while self.match("+", "-"):
            op = self.previous()
            expr = Binary(op.line, op.column, expr, op.kind, self.factor())
        return expr

    def factor(self):
        expr = self.unary()
        while self.match("*", "/", "%"):
            op = self.previous()
            expr = Binary(op.line, op.column, expr, op.kind, self.unary())
        return expr

    def unary(self):
        if self.match("-", "NOT"):
            op = self.previous()
            return Unary(op.line, op.column, op.kind.lower(), self.unary())
        return self.call()

    def call(self):
        expr = self.primary()
        while True:
            if self.match("("):
                args = []
                if not self.check(")"):
                    while True:
                        args.append(self.expression())
                        if not self.match(","):
                            break
                end = self.consume(")", "Expected ')' after arguments")
                expr = Call(end.line, end.column, expr, args)
            elif self.match("."):
                name = self.consume("IDENT", "Expected property name after '.'")
                expr = Get(name.line, name.column, expr, name.value)
            elif self.match("["):
                index = self.expression()
                end = self.consume("]", "Expected ']' after index")
                expr = Index(end.line, end.column, expr, index)
            else:
                break
        return expr

    def primary(self):
        if self.match("NUMBER", "STRING", "FSTRING", "BOOL", "NULL"):
            t = self.previous()
            return Literal(t.line, t.column, (t.kind, t.value) if t.kind == "FSTRING" else t.value)
        if self.match("IDENT"):
            t = self.previous()
            return Variable(t.line, t.column, t.value)
        if self.match("("):
            expr = self.expression()
            self.consume(")", "Expected ')' after expression")
            return expr
        if self.match("["):
            token = self.previous()
            elements = []
            if not self.check("]"):
                while True:
                    elements.append(self.expression())
                    if not self.match(","):
                        break
            self.consume("]", "Expected ']' after array elements")
            return ArrayLiteral(token.line, token.column, elements)
        t = self.peek()
        raise ParseError("Expected expression", t.line, t.column, self.filename)
