from .errors import RuntimeErrorSomax

def type_matches(type_name, value):
    if type_name in ("int", "INT"):
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name in ("float", "double", "FLOAT", "DOUBLE"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name in ("string", "STRING"):
        return isinstance(value, str)
    if type_name in ("char", "CHAR"):
        return isinstance(value, str) and len(value) == 1
    if type_name in ("bool", "BOOL"):
        return isinstance(value, bool)
    if type_name in ("bit", "BIT"):
        return isinstance(value, (bool, int)) and value in (0, 1, True, False)
    if type_name in ("array", "ARRAY"):
        return isinstance(value, list)
    return False

def validate(type_name, value, name):
    if not type_matches(type_name, value):
        raise RuntimeErrorSomax(f"Type mismatch for '{name}': expected {type_name}, got {type(value).__name__}")
    if type_name in ("float", "double", "FLOAT", "DOUBLE") and isinstance(value, int):
        return float(value)
    if type_name in ("bit", "BIT") and isinstance(value, bool):
        return int(value)
    return value
