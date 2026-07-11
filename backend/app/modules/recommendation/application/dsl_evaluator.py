from __future__ import annotations

from app.modules.recommendation.domain.errors import RecommendationEvaluationError


def eval_expression(expression: str, context: dict[str, object]) -> object:
    expr = expression.strip()

    if not expr:
        raise RecommendationEvaluationError("empty expression")

    lowered = expr.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    if _is_number(expr):
        return float(expr)

    if expr.startswith('"') and expr.endswith('"') and len(expr) >= 2:
        return expr[1:-1]

    if "(" not in expr:
        return context.get(expr, 0.0)

    if not expr.endswith(")"):
        raise RecommendationEvaluationError(f"invalid expression syntax: {expression}")

    fn_name, raw_args = expr.split("(", 1)
    fn_name = fn_name.strip().lower()
    arg_tokens = _split_args(raw_args[:-1])
    args = [eval_expression(token, context) for token in arg_tokens if token.strip()]

    return _apply_function(fn_name, args)


def _apply_function(fn_name: str, args: list[object]) -> object:
    if fn_name == "add":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) + _to_float(args[1])
    if fn_name == "sub":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) - _to_float(args[1])
    if fn_name == "mul":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) * _to_float(args[1])
    if fn_name == "div":
        _require_arity(fn_name, args, 2)
        denom = _to_float(args[1])
        if denom == 0:
            return 0.0
        return _to_float(args[0]) / denom

    if fn_name == "gt":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) > _to_float(args[1])
    if fn_name == "gte":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) >= _to_float(args[1])
    if fn_name == "lt":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) < _to_float(args[1])
    if fn_name == "lte":
        _require_arity(fn_name, args, 2)
        return _to_float(args[0]) <= _to_float(args[1])
    if fn_name == "eq":
        _require_arity(fn_name, args, 2)
        return _normalize(args[0]) == _normalize(args[1])
    if fn_name == "neq":
        _require_arity(fn_name, args, 2)
        return _normalize(args[0]) != _normalize(args[1])

    if fn_name == "and":
        return all(_to_bool(item) for item in args)
    if fn_name == "or":
        return any(_to_bool(item) for item in args)
    if fn_name == "not":
        _require_arity(fn_name, args, 1)
        return not _to_bool(args[0])

    raise RecommendationEvaluationError(f"unsupported function: {fn_name}")


def _split_args(raw: str) -> list[str]:
    args: list[str] = []
    depth = 0
    start = 0
    for idx, char in enumerate(raw):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(raw[start:idx].strip())
            start = idx + 1
    tail = raw[start:].strip()
    if tail:
        args.append(tail)
    return args


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _to_float(value: object) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and _is_number(value):
        return float(value)
    raise RecommendationEvaluationError(f"value is not numeric: {value}")


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value) != 0.0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no", ""}:
            return False
    return bool(value)


def _normalize(value: object) -> object:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if _is_number(lowered):
            return float(lowered)
        return lowered
    return value


def _require_arity(fn_name: str, args: list[object], size: int) -> None:
    if len(args) != size:
        raise RecommendationEvaluationError(f"function '{fn_name}' expects {size} args, got {len(args)}")
