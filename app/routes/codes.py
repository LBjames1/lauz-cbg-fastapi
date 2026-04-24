from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Code
from ..schemas import CodeCreate, CodeUpdate, CodeResponse, ApiResponse
from ..utils.pagination import Pagination
from ..config import settings

router = APIRouter()

# 注意：具体路由必须放在参数路由之前，避免路径冲突

# 新增：按实体类型查询的接口（具体路由，必须放在前面）
@router.get("/entity-types", response_model=ApiResponse)
def get_entity_types(db: Session = Depends(get_db)):
    """获取所有实体类型（包含中文名称）"""
    # 查询所有不同的 entity_type 及其对应的名称
    result = db.query(
        Code.entity_type,
        Code.entity_type_name
    ).distinct().all()
    
    # 构建详细的实体类型列表
    entity_types = [
        {
            "type": item[0],
            "name": item[1] or ""  # 如果名称为空则返回空字符串
        }
        for item in result if item[0]  # 过滤掉 entity_type 为空的记录
    ]
    
    return {
        "code": 200,
        "message": "",
        "data": entity_types
    }

@router.get("/entity/{entity_type}/code-types", response_model=ApiResponse)
def get_code_types(entity_type: str, db: Session = Depends(get_db)):
    """获取某个实体类型下的所有编码类型（包含中文名称）"""
    # 查询指定 entity_type 下的所有不同的 code_type
    result = db.query(
        Code.code_type,
        Code.code_type_name
    ).filter(
        Code.entity_type == entity_type
    ).distinct().all()
    
    # 为每个 code_type 查询一个示例编码对象
    code_objects = []
    for code_type, code_type_name in result:
        if code_type:  # 过滤掉 code_type 为空的记录
            # 查询该类型的第一个编码作为代表
            sample_code = db.query(Code).filter(
                Code.entity_type == entity_type,
                Code.code_type == code_type
            ).first()
            
            if sample_code:
                code_objects.append(CodeResponse.model_validate(sample_code).model_dump())
    
    return {
        "code": 200,
        "message": "",
        "data": code_objects
    }

@router.get("/entity/{entity_type}/codes/{code_type}/page", response_model=ApiResponse)
def get_codes_by_entity_and_type(
    entity_type: str, 
    code_type: str, 
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取具体编码数据（分页查询）"""
    # 计算跳过的记录数
    skip = (page - 1) * limit
    
    query = db.query(Code).filter(
        Code.entity_type == entity_type, 
        Code.code_type == code_type
    ).order_by(Code.sort_order)
    
    # 分页处理
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    # 使用 model_validate 转换为 Pydantic 模型列表
    items_dict = [CodeResponse.model_validate(item).model_dump() for item in items]
    
    return {
        "code": 200,
        "message": "",
        "data": {
            "total": total,
            "items": items_dict,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }

@router.get("/entity/{entity_type}/codes/{code_type}/all", response_model=ApiResponse)
def get_all_codes_by_entity_and_type(
    entity_type: str, 
    code_type: str, 
    db: Session = Depends(get_db)
):
    """获取具体编码数据（全部，不分页）"""
    query = db.query(Code).filter(
        Code.entity_type == entity_type, 
        Code.code_type == code_type
    ).order_by(Code.sort_order)
    
    # 直接查询所有数据
    all_items = query.all()
    
    # 使用 model_validate 转换为 Pydantic 模型列表
    codes_list = [CodeResponse.model_validate(item).model_dump() for item in all_items]
    
    return {
        "code": 200,
        "message": "",
        "data": codes_list
    }

@router.post("/codes", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_code(code: CodeCreate, db: Session = Depends(get_db)):
    """创建编码"""
    # 确保 entity_type 存在
    if not code.entity_type:
        raise HTTPException(status_code=400, detail="entity_type is required")
    
    db_code = Code(
        entity_type=code.entity_type,
        entity_type_name=code.entity_type_name,
        code_type=code.code_type,
        code_type_name=code.code_type_name,
        code_value=code.code_value,
        display_name=code.display_name,
        sort_order=code.sort_order or 0
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    
    # 使用 model_validate 转换为 Pydantic 模型
    code_response = CodeResponse.model_validate(db_code)
    return {
        "code": 201,
        "message": "Code created successfully",
        "data": code_response
    }

@router.get("/", response_model=ApiResponse)
def list_codes(
    skip: int = 0,
    limit: int = 10,
    code_type: Optional[str] = Query(None),
    display_name: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取编码列表（支持搜索过滤和分页）"""
    # 构建过滤条件
    filters = {}
    if code_type:
        filters["code_type"] = code_type
    if display_name:
        filters["display_name"] = display_name
    if entity_type:
        filters["entity_type"] = entity_type
    
    pagination = Pagination(db, Code, skip, limit)
    result = pagination.get_paginated_response(filters)
    
    return {
        "code": 200,
        "message": "",
        "data": result
    }

@router.get("/{code_id}", response_model=ApiResponse)
def get_code(code_id: int, db: Session = Depends(get_db)):
    """获取编码详情"""
    code = db.query(Code).filter(Code.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    # 使用 model_validate 转换为 Pydantic 模型
    code_response = CodeResponse.model_validate(code)
    return {
        "code": 200,
        "message": "",
        "data": code_response
    }

@router.put("/{code_id}", response_model=ApiResponse)
def update_code(code_id: int, code: CodeUpdate, db: Session = Depends(get_db)):
    """更新编码"""
    db_code = db.query(Code).filter(Code.id == code_id).first()
    if not db_code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    for key, value in code.dict(exclude_unset=True).items():
        setattr(db_code, key, value)
    
    db.commit()
    db.refresh(db_code)
    
    # 使用 model_validate 转换为 Pydantic 模型
    code_response = CodeResponse.model_validate(db_code)
    return {
        "code": 200,
        "message": "Code updated successfully",
        "data": code_response
    }

@router.delete("/{code_id}", response_model=ApiResponse)
def delete_code(code_id: int, db: Session = Depends(get_db)):
    """删除编码"""
    code = db.query(Code).filter(Code.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    db.delete(code)
    db.commit()
    return {
        "code": 200,
        "message": "Code deleted successfully",
        "data": None
    }