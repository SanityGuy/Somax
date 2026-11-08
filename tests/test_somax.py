import unittest
import tempfile
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from somax.lexer import Lexer
from somax.parser import Parser
from somax.interpreter import Runtime

def execute(source, folder=None):
    program = Parser(Lexer(source).tokenize()).parse()
    runtime = Runtime(base_dir=folder)
    output = StringIO()
    with redirect_stdout(output):
        runtime.run(program.statements)
    return output.getvalue().splitlines(), runtime

class SomaxTests(unittest.TestCase):
    def test_variables_and_math(self):
        out, _ = execute('int x = 10; int y = 20; out.print(x + y);')
        self.assertEqual(out, ["30"])

    def test_if_else(self):
        out, _ = execute('int x = 4; if x > 3 then out.print("yes"); else out.print("no");')
        self.assertEqual(out, ["yes"])

    def test_arrays(self):
        out, _ = execute('array a = ["A", "B"]; out.print(a[0]); out.print(a.length()); out.print(a.deserialize());')
        self.assertEqual(out, ["A", "2", "AB"])

    def test_functions_and_scope(self):
        out, _ = execute('function add(int a, int b) { int c = a + b; return c; } out.print(add(2, 3));')
        self.assertEqual(out, ["5"])

    def test_for_loop(self):
        out, _ = execute('for (int i = 0; i < 3; i = i + 1) then out.print(i);')
        self.assertEqual(out, ["0", "1", "2"])

    def test_while_loop(self):
        out, _ = execute('int i = 0; while i < 2 then { out.print(i); i = i + 1; }')
        self.assertEqual(out, ["0", "1"])

    def test_native_modules(self):
        out, _ = execute('import math; import text; out.print(math.sqrt(81)); out.print(text.upper("somax"));')
        self.assertEqual(out, ["9.0", "SOMAX"])

    def test_nested_arrays_and_mutation(self):
        out, _ = execute('array values = [[1, 2], [3, 4]]; out.print(values[1][0]); values[0].add(9); out.print(values[0]);')
        self.assertEqual(out, ["3", "1, 2, 9"])

    def test_string_methods(self):
        out, _ = execute('string value = "  Somax  "; out.print(value.trim().upper()); out.print(value.contains("max")); out.print(value.replace("Somax", "Nova"));')
        self.assertEqual(out, ["SOMAX", "true", "  Nova  "])

    def test_recursion(self):
        out, _ = execute('function factorial(int n) { if n <= 1 then return 1; return n * factorial(n - 1); } out.print(factorial(5));')
        self.assertEqual(out, ["120"])

    def test_local_module(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "greetings.smx").write_text('function hi(string name) { out.print(f"Hi, {name}!"); }', encoding="utf-8")
            out, _ = execute('import greetings; greetings.hi("Ada");', folder)
            self.assertEqual(out, ["Hi, Ada!"])

if __name__ == "__main__":
    unittest.main()
