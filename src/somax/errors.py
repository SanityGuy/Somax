class SomaxError(Exception):
    def __init__(self, message, line=None, column=None, filename=None):
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        location = ""
        if filename:
            location += filename
        if line is not None:
            location += f":{line}"
            if column is not None:
                location += f":{column}"
        prefix = f"{location}: " if location else ""
        super().__init__(prefix + message)


class LexerError(SomaxError):
    pass


class ParseError(SomaxError):
    pass


class RuntimeErrorSomax(SomaxError):
    pass
