from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Pattern, Image
from ..schemas import PatternCreate, PatternUpdate, PatternResponse, ApiResponse
from ..utils.pagination import Pagination
from ..config import settings

router = APIRouter()

@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_pattern(pattern: PatternCreate, db: Session = Depends(get_db)):
    """创建纸样（包含编码和图片关联）"""
    # 提取关联字段
    category_id = pattern.category_id
    style_ids = pattern.style_ids or []
    image_ids = pattern.image_ids or []
    
    # 创建纸样主体（排除关联字段）
    pattern_dict = pattern.dict(exclude={'category_id', 'style_ids', 'images'})
    db_pattern = Pattern(**pattern_dict)
    db.add(db_pattern)
    db.commit()
    db.refresh(db_pattern)
    
    # 处理编码关联
    if category_id:
        db_pattern.category_id = category_id
    
    # 处理款式多对多关联
    if style_ids:
        from ..models import PatternStyle
        for style_id in style_ids:
            pattern_style = PatternStyle(pattern_id=db_pattern.id, code_id=style_id)
            db.add(pattern_style)
    
    # 处理图片关联
    if image_ids:
        for image_ref in image_ids:
            # 更新图片的entity_id为新创建的纸样ID
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = db_pattern.id
                db_image.entity_type = "pattern"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_pattern)
    
    return {
        "code": 201,
        "message": "Pattern created successfully",
        "data": db_pattern
    }

@router.get("/{pattern_id}", response_model=ApiResponse)
def get_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """获取纸样详情（包含关联的编码和图片信息）"""
    pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # 加载关联的图片信息
    pattern.images = db.query(Image).filter(
        Image.entity_type == "pattern",
        Image.entity_id == pattern_id
    ).all()
    
    return {
        "code": 200,
        "message": "",
        "data": pattern
    }

@router.get("", response_model=ApiResponse)
def list_patterns(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="纸样名称"),
    category_id: Optional[int] = Query(None, description="品类 ID"),
    style_ids: Optional[List[int]] = Query(None, description="款式 ID 列表（支持多个）"),
    # 通用查询参数
    code_type: Optional[str] = Query(None, description="编码类型（category/style 等）"),
    code_id: Optional[int] = Query(None, description="编码 ID，与 code_type 配合使用"),
    db: Session = Depends(get_db)
):
    """获取纸样列表（支持搜索过滤和分页）"""
    # 计算跳过的记录数
    skip = (page - 1) * limit
    
    # 直接查询数据
    from ..utils.query_helpers import filter_by_code_type, filter_by_code_ids
    query = db.query(Pattern)
    
    # 构建基础过滤条件
    filters = {}
    if name:
        filters["name"] = name
    if category_id:
        filters["category_id"] = category_id
    
    # 处理通用查询参数（动态字段查询）
    if code_type and code_id:
        query = filter_by_code_type(query, Pattern, db, code_type, code_id, entity_type='pattern')
    
    # 处理多对多关系列表
    if style_ids:
        query = filter_by_code_ids(query, Pattern, db, 'style', style_ids, entity_type='pattern')
    
    # 应用基础过滤条件
    for key, value in filters.items():
        if hasattr(Pattern, key):
            if isinstance(value, str):
                query = query.filter(getattr(Pattern, key).like(f"%{value}%"))
            else:
                query = query.filter(getattr(Pattern, key) == value)
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据并加载图片
    patterns = query.offset(skip).limit(limit).all()
    
    # 为每个纸样加载关联的图片信息
    for pattern in patterns:
        pattern.images = db.query(Image).filter(
            Image.entity_type == "pattern",
            Image.entity_id == pattern.id
        ).all()
    
    # 转换为标准分页格式
    return {
        "code": 200,
        "message": "",
        "data": {
            "items": patterns,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }

@router.put("/{pattern_id}", response_model=ApiResponse)
def update_pattern(pattern_id: int, pattern: PatternUpdate, db: Session = Depends(get_db)):
    """更新纸样（包含编码和图片关联）"""
    db_pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # 提取关联字段
    category_id = getattr(pattern, 'category_id', None)
    style_ids = getattr(pattern, 'style_ids', None)
    image_ids = getattr(pattern, 'image_ids', None)
    
    # 更新基本字段
    update_dict = pattern.dict(exclude_unset=True, exclude={'category_id', 'style_ids', 'images'})
    for key, value in update_dict.items():
        setattr(db_pattern, key, value)
    
    # 更新编码关联
    if category_id is not None:
        db_pattern.category_id = category_id
    
    # 更新款式多对多关联
    if style_ids is not None:
        from ..models import PatternStyle
        # 删除现有关联
        db.query(PatternStyle).filter(PatternStyle.pattern_id == pattern_id).delete()
        # 添加新关联
        for style_id in style_ids:
            pattern_style = PatternStyle(pattern_id=pattern_id, code_id=style_id)
            db.add(pattern_style)
    
    # 更新图片关联
    if image_ids is not None:
        # 更新现有图片的entity_id
        for image_ref in image_ids:
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = pattern_id
                db_image.entity_type = "pattern"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_pattern)
    return {
        "code": 200,
        "message": "Pattern updated successfully",
        "data": db_pattern
    }

@router.get("/count", response_model=ApiResponse)
def get_patterns_count(db: Session = Depends(get_db)):
    """获取纸样总数"""
    count = db.query(Pattern).count()
    return {
        "code": 200,
        "message": "",
        "data": {
            "count": count
        }
    }

@router.delete("/{pattern_id}", response_model=ApiResponse)
def delete_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """删除纸样"""
    pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    db.delete(pattern)
    db.commit()
    return {
        "code": 200,
        "message": "Pattern deleted successfully",
        "data": None
    }