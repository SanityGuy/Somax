# Somax 1.0

Somax is a small, statically typed, interpreted programming language with Java-style declarations, readable control flow, arrays, functions, modules, and a built-in standard library.

## Requirements

- Python 3.10 or newer

## Install

From this directory:

```bash
python -m pip install -e .
```

Run a program:

```bash
somax examples/hello.smx
```

You can also run it without installing:

```bash
PYTHONPATH=src python -m somax.main examples/hello.smx
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m somax.main examples/hello.smx
```

## Basic syntax

```java
string developer = "Souyan";
int version = 1;
bool released = true;

out.print(f"Hello, {developer}!");

if version >= 1 then {
    out.print("Released!");
} else {
    out.print("Not released yet.");
}
```

Every declaration and expression statement ends with `;`. A `then` body can be one statement or a brace-delimited block.

## Types

| Type | Meaning | Default |
|---|---|---|
| `int` | Integer | `0` |
| `float` | Floating point | `0.0` |
| `double` | Floating point | `0.0` |
| `string` | Text | `""` |
| `char` | One-character string | `"\0"` |
| `bool` | Boolean | `false` |
| `bit` | Integer restricted to `0` or `1` | `0` |
| `array` | Mutable list | `[]` |

Variables are case-sensitive and cannot be redeclared in the same scope. Assignments are type-checked.

## Operators

Arithmetic: `+ - * / %`

Comparison: `== != > >= < <=`

Logic: `and or not`

Assignment: `=`

## Arrays

```java
array names = ["Ada", "Linus", "Grace"];
out.print(names[0]);
out.print(names.length());
out.print(names.findExact("Grace"));
names.add("Margaret");
names.remove("Linus");
out.print(names.deserialize());
out.print(names.space());
```

`findExact()` returns the zero-based index, or `-1` when not found. `deserialize()` joins array elements without a separator. `space()` joins them with one space. Arrays can contain nested arrays.

## Strings

```java
string message = "  Hello Somax  ";
out.print(message.upper());
out.print(message.lower());
out.print(message.trim());
out.print(message.contains("Somax"));
out.print(message.replace("Somax", "World"));
out.print(message.split(" "));
```

String methods include `length`, `upper`, `lower`, `trim`, `contains`, `replace`, `split`, and `space`.

Formatted strings use `f"..."`:

```java
string name = "Souyan";
int age = 15;
out.print(f"{name} is {age}");
```

Interpolation currently supports variable names, simple dotted properties, and numeric array indexes.

## Functions

```java
function multiply(int x, int y) {
    return x * y;
}

int result = multiply(6, 7);
out.print(result);
```

Functions support typed parameters, local scope, return values, and recursion.

## Loops

```java
for (int i = 0; i < 5; i = i + 1) then {
    out.print(i);
}

int counter = 0;
while counter < 3 then {
    out.print(counter);
    counter = counter + 1;
}
```

## Modules

Native modules:

```java
import math;
import text;
import convert;

out.print(math.sqrt(144));
out.print(text.upper("somax"));
out.print(convert.toInt("42"));
```

Available modules:

- `math`: `sqrt`, `pow`, `abs`, `round`, `floor`, `ceil`
- `text`: `upper`, `lower`, `trim`, `replace`, `contains`
- `convert`: `toInt`, `toFloat`, `toString`
- `console`: `read`, `write`, `clear`
- `file`: `read`, `write`, `exists`

Local modules are `.smx` files in the same project directory:

```java
import utilities;
utilities.greet("Souyan");
```

The importer rejects paths that escape the project directory and detects circular imports. Local modules execute in their own module scope.

## File module safety

`file.read`, `file.write`, and `file.exists` only access paths inside the directory containing the entry `.smx` file. Do not run untrusted Somax programs because `console.read` and file operations can interact with the local environment.

## Implementation

The interpreter is written in Python and uses a lexer, recursive-descent parser, AST nodes, runtime environments, and an interpreter. The architecture is intended to make a later C implementation possible against the same language specification and tests.

## Known 1.0 limitations

- No classes, structs, exceptions, pointers, generics, or concurrency.
- No static semantic-analysis pass yet; type checks occur during execution.
- No `break` or `continue`.
- No implicit numeric conversion except assigning an integer to `float` or `double`.
- Module imports are namespace-based and local modules use one file per module.
- F-strings intentionally support a limited interpolation grammar.
- Error locations are strongest for lexer and parser errors; some runtime errors currently lack source coordinates.

Somax 1.0 is an initial language release, not a production sandbox. Treat programs as trusted code.
