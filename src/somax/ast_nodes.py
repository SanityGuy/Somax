from dataclasses import dataclass

@dataclass
class Node:
    line: int
    column: int

@dataclass
class Program(Node):
    statements: list

@dataclass
class Block(Node):
    statements: list

@dataclass
class VarDecl(Node):
    type_name: str
    name: str
    initializer: object

@dataclass
class FunctionDecl(Node):
    name: str
    params: list
    body: Block

@dataclass
class ImportDecl(Node):
    name: str
    alias: str

@dataclass
class IfStmt(Node):
    condition: object
    then_branch: object
    else_branch: object

@dataclass
class WhileStmt(Node):
    condition: object
    body: object

@dataclass
class ForStmt(Node):
    initializer: object
    condition: object
    update: object
    body: object

@dataclass
class ReturnStmt(Node):
    value: object

@dataclass
class ExprStmt(Node):
    expression: object

@dataclass
class Literal(Node):
    value: object

@dataclass
class Variable(Node):
    name: str

@dataclass
class ArrayLiteral(Node):
    elements: list

@dataclass
class Unary(Node):
    operator: str
    right: object

@dataclass
class Binary(Node):
    left: object
    operator: str
    right: object

@dataclass
class Assign(Node):
    target: object
    value: object

@dataclass
class Call(Node):
    callee: object
    arguments: list

@dataclass
class Get(Node):
    object: object
    name: str

@dataclass
class Index(Node):
    object: object
    index: object
