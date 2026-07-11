from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.business.infrastructure.container import build_customer_container
from app.modules.business.infrastructure.product_container import build_product_container
from app.modules.imports.application.use_cases import ImportCsvUseCase
from app.modules.imports.infrastructure.repositories import ImportRepository


@dataclass(slots=True)
class ImportsContainer:
    import_csv: ImportCsvUseCase


def build_imports_container(session: Session) -> ImportsContainer:
    repository = ImportRepository(session=session)
    customer_container = build_customer_container(session)
    product_container = build_product_container(session)

    return ImportsContainer(
        import_csv=ImportCsvUseCase(
            repository=repository,
            upsert_customer=customer_container.upsert_customer,
            upsert_product=product_container.upsert_product,
        )
    )
