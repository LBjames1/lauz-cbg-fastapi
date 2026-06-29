from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Item, Image
from ..schemas import ItemCreate, ItemUpdate, ItemResponse, ApiResponse
from ..utils.pagination import Pagination
from ..utils.query_helpers import serialize_model, serialize_list
from ..config import settings

router = APIRouter()

@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_item(request: Request, item: ItemCreate, db: Session = Depends(get_db)):
    """创建物品（包含编码和图片关联）"""
    # 提取关联字段
    type_id = item.type_id
    image_ids = item.image_ids or []
    
    # 创建物品主体（排除关联字段）
    item_dict = item.dict(exclude={'type_id', 'image_ids', 'images'})
    db_item = Item(**item_dict)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # 处理编码关联
    if type_id:
        db_item.type_id = type_id
    
    # 处理图片关联
    if image_ids:
        for image_ref in image_ids:
            # 更新图片的entity_id为新创建的物品ID
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = db_item.id
                db_image.entity_type = "item"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_item)
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    item_dict = serialize_model(db_item, base_url)
    
    return {
        "code": 201,
        "message": "Item created successfully",
        "data": item_dict
    }

@router.get("/{item_id}", response_model=ApiResponse)
def get_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    """获取物品详情（包含关联的编码和图片信息）"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 加载关联的图片信息
    item.images = db.query(Image).filter(
        Image.entity_type == "item",
        Image.entity_id == item_id
    ).all()
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    item_dict = serialize_model(item, base_url)
    
    return {
        "code": 200,
        "message": "",
        "data": item_dict
    }

@router.get("", response_model=ApiResponse)
def list_items(
    request: Request,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="物品名称"),
    purchase_channel: Optional[str] = Query(None, description="购买渠道"),
    type_id: Optional[int] = Query(None, description="类型 ID"),
    # 通用查询参数
    code_type: Optional[str] = Query(None, description="编码类型（type 等）"),
    code_id: Optional[int] = Query(None, description="编码 ID，与 code_type 配合使用"),
    db: Session = Depends(get_db)
):
    """获取物品列表（支持搜索过滤和分页）"""
    # 计算跳过的记录数
    skip = (page - 1) * limit
    
    # 直接查询数据
    from ..utils.query_helpers import filter_by_code_type
    query = db.query(Item)
    
    # 构建基础过滤条件
    filters = {}
    if name:
        filters["name"] = name
    if purchase_channel:
        filters["purchase_channel"] = purchase_channel
    if type_id:
        filters["type_id"] = type_id
    
    # 处理通用查询参数（动态字段查询）
    if code_type and code_id:
        query = filter_by_code_type(query, Item, db, code_type, code_id, entity_type='item')
    
    # 应用基础过滤条件
    for key, value in filters.items():
        if hasattr(Item, key):
            if isinstance(value, str):
                query = query.filter(getattr(Item, key).like(f"%{value}%"))
            else:
                query = query.filter(getattr(Item, key) == value)
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据并加载图片
    items = query.offset(skip).limit(limit).all()
    
    # 为每个物品加载关联的图片信息
    for item in items:
        item.images = db.query(Image).filter(
            Image.entity_type == "item",
            Image.entity_id == item.id
        ).all()
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    serialized_items = serialize_list(items, base_url)
    
    # 转换为标准分页格式
    return {
        "code": 200,
        "message": "",
        "data": {
            "items": serialized_items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }

@router.put("/{item_id}", response_model=ApiResponse)
def update_item(item_id: int, request: Request, item: ItemUpdate, db: Session = Depends(get_db)):
    """更新物品（包含编码和图片关联）"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 提取关联字段
    type_id = getattr(item, 'type_id', None)
    image_ids = getattr(item, 'image_ids', None)
    
    # 更新基本字段
    update_dict = item.dict(exclude_unset=True, exclude={'type_id', 'image_ids', 'images'})
    for key, value in update_dict.items():
        setattr(db_item, key, value)
    
    # 更新编码关联
    if type_id is not None:
        db_item.type_id = type_id
    
    # 更新图片关联
    if image_ids is not None:
        # 更新现有图片的entity_id
        for image_ref in image_ids:
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = item_id
                db_image.entity_type = "item"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_item)
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    item_dict = serialize_model(db_item, base_url)
    
    return {
        "code": 200,
        "message": "Item updated successfully",
        "data": item_dict
    }

@router.get("/count", response_model=ApiResponse)
def get_items_count(db: Session = Depends(get_db)):
    """获取物品总数"""
    count = db.query(Item).count()
    return {
        "code": 200,
        "message": "",
        "data": {
            "count": count
        }
    }

@router.delete("/{item_id}", response_model=ApiResponse)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """删除物品"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {
        "code": 200,
        "message": "Item deleted successfully",
        "data": None
    }