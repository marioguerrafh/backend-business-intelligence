from collections import defaultdict, deque

from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition
from app.modules.kpi.domain.formula_engine_errors import FormulaDependencyError


class FormulaDependencyResolver:
    def resolve_order(self, formulas: dict[str, FormulaDefinition]) -> list[str]:
        inbound: dict[str, int] = {formula_id: 0 for formula_id in formulas}
        graph: dict[str, set[str]] = defaultdict(set)

        for formula_id, definition in formulas.items():
            for dependency in self._extract_dependencies(definition):
                if dependency not in formulas:
                    raise FormulaDependencyError(
                        f"formula {formula_id} depends on missing formula {dependency}"
                    )
                if formula_id not in graph[dependency]:
                    graph[dependency].add(formula_id)
                    inbound[formula_id] += 1

        queue: deque[str] = deque([node for node, deg in inbound.items() if deg == 0])
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in graph[node]:
                inbound[neighbor] -= 1
                if inbound[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(formulas):
            raise FormulaDependencyError("cyclic formula dependency detected")
        return order

    def _extract_dependencies(self, definition: FormulaDefinition) -> set[str]:
        dependencies: set[str] = set()
        for metric in definition.input_metrics:
            if metric.startswith("formula:"):
                dependencies.add(metric.removeprefix("formula:"))
            elif metric.startswith("f."):
                dependencies.add(metric)
            elif metric.startswith("formula."):
                dependencies.add(metric.removeprefix("formula."))
        return dependencies

    def dependencies_of(self, definition: FormulaDefinition) -> list[str]:
        return sorted(self._extract_dependencies(definition))
