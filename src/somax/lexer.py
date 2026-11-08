from .tokens import Token
from .errors import LexerError

KEYWORDS = {
    "int", "float", "double", "string", "char", "bool", "bit", "array",
    "function", "return", "if", "else", "while", "for", "then",
    "true", "false", "null", "and", "or", "not", "import", "as"
}

class Lexer:
    def __init__(self, source, filename=None):
        self.source = source
        self.filename = filename
        self.i = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def peek(self, offset=0):
        pos = self.i + offset
        return self.source[pos] if pos < len(self.source) else "\0"

    def advance(self):
        ch = self.peek()
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def add(self, kind, value, line, column):
        self.tokens.append(Token(kind, value, line, column))

    def tokenize(self):
        while self.peek() != "\0":
            ch = self.peek()
            if ch in " \r\t":
                self.advance()
                continue
            if ch == "\n":
                self.advance()
                continue
            if ch == "#" and self.peek(1) == "#":
                while self.peek() not in ("\n", "\0"):
                    self.advance()
                continue
            line, col = self.line, self.column
            if ch.isalpha() or ch == "_":
                if ch == "f" and self.peek(1) in ("'", '"'):
                    self.advance()
                    self.string(line, col, True)
                else:
                    self.identifier(line, col)
            elif ch.isdigit():
                self.number(line, col)
            elif ch in ("'", '"'):
                self.string(line, col, False)
            else:
                self.symbol(line, col)
        self.add("EOF", None, self.line, self.column)
        return self.tokens

    def identifier(self, line, col):
        value = ""
        while self.peek().isalnum() or self.peek() == "_":
            value += self.advance()
        if value == "true":
            self.add("BOOL", True, line, col)
        elif value == "false":
            self.add("BOOL", False, line, col)
        elif value == "null":
            self.add("NULL", None, line, col)
        else:
            self.add(value.upper() if value in KEYWORDS else "IDENT", value, line, col)

    def number(self, line, col):
        value = ""
        while self.peek().isdigit():
            value += self.advance()
        if self.peek() == "." and self.peek(1).isdigit():
            value += self.advance()
            while self.peek().isdigit():
                value += self.advance()
            self.add("NUMBER", float(value), line, col)
        else:
            self.add("NUMBER", int(value), line, col)

    def string(self, line, col, formatted):
        quote = self.advance()
        value = ""
        while self.peek() not in (quote, "\0"):
            ch = self.advance()
            if ch == "\\":
                nxt = self.advance()
                escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", '"': '"'}
                value += escapes.get(nxt, nxt)
            else:
                value += ch
        if self.peek() == "\0":
            raise LexerError("Unterminated string", line, col, self.filename)
        self.advance()
        self.add("FSTRING" if formatted else "STRING", value, line, col)

    def symbol(self, line, col):
        two = self.peek() + self.peek(1)
        if two in ("==", "!=", "<=", ">=", "++", "--"):
            self.advance()
            self.advance()
            self.add(two, two, line, col)
            return
        ch = self.advance()
        if ch in "+-*/%(){}[];,.:=<>":
            self.add(ch, ch, line, col)
            return
        raise LexerError(f"Unexpected character {ch!r}", line, col, self.filename)
