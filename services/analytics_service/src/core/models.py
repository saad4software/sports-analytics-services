from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class IResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: T | None = None
