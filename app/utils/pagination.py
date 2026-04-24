from typing import Type, Generic, TypeVar
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .schemas import PaginationResponse

T = TypeVar('T')

class Pagination(Generic[T]):
    def __init__(self, db: Session, model: Type[T], skip: int = 0, limit: int = 10):
        self.db = db
        self.model = model
        self.skip = skip
        self.limit = limit
    
    def get_total(self) -> int:
        """获取总数"""
        return self.db.query(func.count()).select_from(self.model).scalar()
    
    def get_items(self, filters: dict = None) -> list:
        """获取分页数据"""
        query = self.db.query(self.model)
        
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, str):
                        query = query.filter(getattr(self.model, key).like(f"%{value}%"))
                    else:
                        query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(self.skip).limit(self.limit).all()
    
    def get_paginated_response(self, filters: dict = None) -> PaginationResponse:
        """获取分页响应"""
        total = self.get_total()
        items = self.get_items(filters)
        
        # 转换为字典列表
        items_dict = []
        for item in items:
            if hasattr(item, '__dict__'):
                item_dict = item.__dict__.copy()
                item_dict.pop('_sa_instance_state', None)
                items_dict.append(item_dict)
        
        return PaginationResponse(
            total=total,
            page=self.skip // self.limit + 1,
            page_size=self.limit,
            items=items_dict
        )