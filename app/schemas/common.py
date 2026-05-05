from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    status: bool
    message: str
    data: Optional[T] = None


def success_response(data: Any = None, message: str = "Success") -> dict:
    return {"status": True, "message": message, "data": data}


def error_response(message: str = "Failure", data: Any = None) -> dict:
    return {"status": False, "message": message, "data": data}
