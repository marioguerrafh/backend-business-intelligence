from dataclasses import dataclass

from app.modules.kpi.domain.formula_engine_errors import FormulaSyntaxError


@dataclass(slots=True, frozen=True)
class NumberNode:
    value: float


@dataclass(slots=True, frozen=True)
class IdentifierNode:
    name: str


@dataclass(slots=True, frozen=True)
class CallNode:
    function: str
    args: tuple[object, ...]


class FormulaParser:
    def parse(self, expression: str) -> object:
        parser = _ParserState(expression)
        node = parser.parse_expression()
        parser.skip_ws()
        if not parser.is_eof():
            raise FormulaSyntaxError(f"unexpected token at index {parser.idx}")
        return node


class _ParserState:
    def __init__(self, source: str) -> None:
        self.source = source
        self.idx = 0

    def is_eof(self) -> bool:
        return self.idx >= len(self.source)

    def current(self) -> str:
        if self.is_eof():
            return ""
        return self.source[self.idx]

    def skip_ws(self) -> None:
        while not self.is_eof() and self.current().isspace():
            self.idx += 1

    def parse_expression(self) -> object:
        self.skip_ws()
        if self.is_eof():
            raise FormulaSyntaxError("empty expression")

        char = self.current()
        if char.isdigit() or char in "-.":
            return self.parse_number()

        identifier = self.parse_identifier()
        self.skip_ws()
        if self.current() != "(":
            return IdentifierNode(name=identifier)

        self.idx += 1
        args: list[object] = []
        self.skip_ws()
        if self.current() == ")":
            self.idx += 1
            return CallNode(function=identifier, args=tuple(args))

        while True:
            args.append(self.parse_expression())
            self.skip_ws()
            if self.current() == ",":
                self.idx += 1
                self.skip_ws()
                continue
            if self.current() == ")":
                self.idx += 1
                break
            raise FormulaSyntaxError(f"expected ',' or ')' at index {self.idx}")
        return CallNode(function=identifier, args=tuple(args))

    def parse_identifier(self) -> str:
        self.skip_ws()
        start = self.idx
        while not self.is_eof() and (self.current().isalnum() or self.current() in "._:"):
            self.idx += 1
        value = self.source[start:self.idx]
        if not value:
            raise FormulaSyntaxError(f"expected identifier at index {self.idx}")
        return value

    def parse_number(self) -> NumberNode:
        self.skip_ws()
        start = self.idx
        if self.current() == "-":
            self.idx += 1
        dot_count = 0
        while not self.is_eof() and (self.current().isdigit() or self.current() == "."):
            if self.current() == ".":
                dot_count += 1
            self.idx += 1
        if dot_count > 1:
            raise FormulaSyntaxError(f"invalid number at index {start}")
        raw = self.source[start:self.idx]
        try:
            return NumberNode(value=float(raw))
        except ValueError as exc:
            raise FormulaSyntaxError(f"invalid number '{raw}'") from exc
