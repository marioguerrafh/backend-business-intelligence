from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def raise_if_invalid(self) -> None:
        if self.errors:
            raise ValueError("; ".join(self.errors))
