from dataclasses import dataclass


@dataclass(slots=True)
class PageRequest:
    page: int = 1
    page_size: int = 50


@dataclass(slots=True)
class PageResponse:
    total: int
    page: int
    page_size: int
