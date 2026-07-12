# KPI Catalog v1

This document describes the official KPI Catalog as the single source of truth for the platform.

## Structure

Each KPI entry contains:

- `id`
- `code`
- `name`
- `short_name`
- `description`
- `category`
- `subcategory`
- `unit`
- `display_format`
- `precision`
- `icon`
- `color`
- `display_order`
- `formula_id`
- `formula`
- `depends_on`
- `source_tables`
- `business_area`
- `health_ranges`
- `trend_strategy`
- `presentation`
- `tags`
- `owner`

## Versioning

- Version is tracked in `metadata.version`.
- Breaking changes require a new major version.
- Additive changes should preserve existing IDs and aliases.

## How to Add a KPI

1. Choose a stable KPI `id`.
2. Register a unique `code` and `formula_id`.
3. Define the official business meaning.
4. Declare dependencies in `depends_on`.
5. Add health ranges and presentation metadata.
6. Add tests for lookup, validation, and search.

## Best Practices

- Never duplicate KPI meaning under different IDs.
- Keep formulas declarative and traceable.
- Use canonical fields only.
- Prefer official IDs in rules, presentation, and score mapping.
- Version the catalog before changing business meaning.
