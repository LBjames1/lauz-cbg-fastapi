from pydantic import BaseModel
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class PaginationResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int
    page: int
    page_size: int
    items: List[T]
    
    class Config:
        from_attributes = True  # Pydantic v2 语法