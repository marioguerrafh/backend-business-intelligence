from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


class ErrorMapper:
    @staticmethod
    def unprocessable(exc: Exception) -> HTTPException:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    @staticmethod
    def conflict(exc: Exception) -> HTTPException:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    @staticmethod
    def integrity_conflict(message: str, exc: IntegrityError) -> HTTPException:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    @staticmethod
    def not_found(exc: Exception) -> HTTPException:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
