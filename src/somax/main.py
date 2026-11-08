import argparse
import sys
from pathlib import Path
from . import __version__
from .lexer import Lexer
from .parser import Parser
from .interpreter import Runtime
from .errors import SomaxError

def run_file(path):
    file_path = Path(path).resolve()
    source = file_path.read_text(encoding="utf-8")
    tokens = Lexer(source, str(file_path)).tokenize()
    program = Parser(tokens, str(file_path)).parse()
    runtime = Runtime(str(file_path), file_path.parent)
    runtime.run(program.statements)

def main():
    parser = argparse.ArgumentParser(prog="somax", description="Somax programming language")
    parser.add_argument("file", nargs="?", help="Somax source file (.smx)")
    parser.add_argument("--version", action="version", version=f"Somax {__version__}")
    args = parser.parse_args()
    if not args.file:
        parser.print_help()
        return 0
    try:
        run_file(args.file)
        return 0
    except SomaxError as exc:
        print(f"Somax error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Somax error: File not found: {args.file}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
