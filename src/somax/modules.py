import math
from pathlib import Path
from .errors import RuntimeErrorSomax

class NativeModule:
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def get(self, name):
        if name not in self.values:
            raise RuntimeErrorSomax(f"Module '{self.name}' has no member '{name}'")
        return self.values[name]

def native_modules(runtime):
    def require_count(name, args, count):
        if len(args) != count:
            raise RuntimeErrorSomax(f"{name}() expects {count} argument(s), got {len(args)}")
    math_module = NativeModule("math", {
        "sqrt": lambda *a: math.sqrt(a[0]) if len(a) == 1 else _arity("math.sqrt", a, 1),
        "pow": lambda *a: math.pow(a[0], a[1]) if len(a) == 2 else _arity("math.pow", a, 2),
        "abs": lambda *a: abs(a[0]) if len(a) == 1 else _arity("math.abs", a, 1),
        "round": lambda *a: round(*a),
        "floor": lambda *a: math.floor(a[0]) if len(a) == 1 else _arity("math.floor", a, 1),
        "ceil": lambda *a: math.ceil(a[0]) if len(a) == 1 else _arity("math.ceil", a, 1)
    })
    text_module = NativeModule("text", {
        "upper": lambda s: str(s).upper(),
        "lower": lambda s: str(s).lower(),
        "trim": lambda s: str(s).strip(),
        "replace": lambda s, old, new: str(s).replace(str(old), str(new)),
        "contains": lambda s, part: str(part) in str(s)
    })
    convert_module = NativeModule("convert", {
        "toInt": lambda value: int(value),
        "toFloat": lambda value: float(value),
        "toString": lambda value: runtime.stringify(value)
    })
    console_module = NativeModule("console", {
        "read": lambda *a: input(str(a[0]) if a else ""),
        "write": lambda *a: print("".join(runtime.stringify(x) for x in a), end=""),
        "clear": lambda: print("\\033[2J\\033[H", end="")
    })
    file_module = NativeModule("file", {
        "read": lambda path: _safe_read(runtime, path),
        "write": lambda path, content: _safe_write(runtime, path, content),
        "exists": lambda path: _safe_exists(runtime, path)
    })
    return {m.name: m for m in (math_module, text_module, convert_module, console_module, file_module)}

def _arity(name, args, count):
    raise RuntimeErrorSomax(f"{name}() expects {count} argument(s), got {len(args)}")

def _safe_path(runtime, path):
    p = (runtime.base_dir / str(path)).resolve()
    base = runtime.base_dir.resolve()
    if p != base and base not in p.parents:
        raise RuntimeErrorSomax("File path must stay inside the current Somax project directory")
    return p

def _safe_read(runtime, path):
    p = _safe_path(runtime, path)
    return p.read_text(encoding="utf-8")

def _safe_write(runtime, path, content):
    p = _safe_path(runtime, path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(content), encoding="utf-8")
    return True

def _safe_exists(runtime, path):
    return _safe_path(runtime, path).exists()
