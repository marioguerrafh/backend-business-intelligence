from fastapi import HTTPException, status


class TenantGuard:
    @staticmethod
    def assert_payload_company(principal_company_id: str, payload_company_id: str) -> None:
        if payload_company_id != principal_company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="tenant access denied")

    @staticmethod
    def assert_path_company(principal_company_id: str, company_id: str) -> None:
        if company_id != principal_company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="tenant access denied")
