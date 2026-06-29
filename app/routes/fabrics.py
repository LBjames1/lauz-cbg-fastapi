from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Fabric, Image
from ..schemas import FabricCreate, FabricUpdate, FabricResponse, ApiResponse
from ..utils.pagination import Pagination
from ..utils.query_helpers import serialize_model, serialize_list
from ..config import settings

router = APIRouter()

@router.get("/recent", response_model=ApiResponse)
def get_recent_fabrics(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取最近布料分页查询（按创建时间倒序，最近7天数据）"""
    # 计算跳过的记录数
    skip = (page - 1) * limit
    
    # 计算7天前的时间
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # 查询最近7天创建的布料，按创建时间倒序排列
    query = db.query(Fabric).filter(
        Fabric.created_at >= seven_days_ago
    ).order_by(Fabric.created_at.desc())
    
    # 分页处理
    total = query.count()
    fabrics = query.offset(skip).limit(limit).all()
    
    # 为每个布料加载关联的图片信息
    for fabric in fabrics:
        fabric.images = db.query(Image).filter(
            Image.entity_type == "fabric",
            Image.entity_id == fabric.id
        ).all()
    
    # 序列化为字典格式
    serialized_fabrics = serialize_list(fabrics)
    
    result = {
        "items": serialized_fabrics,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit  # 计算总页数
    }
    
    return {
        "code": 200,
        "message": "",
        "data": result
    }

@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_fabric(request: Request, fabric: FabricCreate, db: Session = Depends(get_db)):
    """创建布料（包含编码和图片关联）"""
    # 提取关联字段
    material_id = fabric.material_id
    thickness_id = fabric.thickness_id
    color_ids = fabric.color_ids or []
    image_ids = fabric.image_ids or []
    
    # 创建布料主体（排除关联字段）
    fabric_dict = fabric.dict(exclude={'material_id', 'thickness_id', 'color_ids', 'image_ids', 'images'})
    db_fabric = Fabric(**fabric_dict)
    db.add(db_fabric)
    db.commit()
    db.refresh(db_fabric)
    
    # 处理编码关联
    if material_id:
        db_fabric.material_id = material_id
    if thickness_id:
        db_fabric.thickness_id = thickness_id
    
    # 处理颜色多对多关联
    if color_ids:
        from ..models import FabricColor
        for color_id in color_ids:
            fabric_color = FabricColor(fabric_id=db_fabric.id, code_id=color_id)
            db.add(fabric_color)
    
    # 处理图片关联
    if image_ids:
        for image_ref in image_ids:
            # 更新图片的entity_id为新创建的布料ID
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = db_fabric.id
                db_image.entity_type = "fabric"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_fabric)
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    fabric_dict = serialize_model(db_fabric, base_url)
    
    return {
        "code": 201,
        "message": "Fabric created successfully",
        "data": fabric_dict
    }

@router.get("/{fabric_id}", response_model=ApiResponse)
def get_fabric(fabric_id: int, request: Request, db: Session = Depends(get_db)):
    """获取布料详情（包含关联的编码和图片信息）"""
    fabric = db.query(Fabric).filter(Fabric.id == fabric_id).first()
    if not fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    
    # 加载关联的图片信息
    fabric.images = db.query(Image).filter(
        Image.entity_type == "fabric",
        Image.entity_id == fabric_id
    ).all()
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    fabric_dict = serialize_model(fabric, base_url)
    
    return {
        "code": 200,
        "message": "",
        "data": fabric_dict
    }

@router.get("", response_model=ApiResponse)
def list_fabrics(
    request: Request,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="布料名称"),
    purchase_channel: Optional[str] = Query(None, description="购买渠道"),
    material_id: Optional[int] = Query(None, description="材质 ID"),
    thickness_id: Optional[int] = Query(None, description="厚度 ID"),
    color_ids: Optional[List[int]] = Query(None, description="颜色 ID 列表（支持多个）"),
    width: Optional[str] = Query(None, description="幅宽"),
    length: Optional[str] = Query(None, description="长度"),
    # 通用查询参数
    code_type: Optional[str] = Query(None, description="编码类型（material/thickness/color 等）"),
    code_id: Optional[int] = Query(None, description="编码 ID，与 code_type 配合使用"),
    db: Session = Depends(get_db)
):
    """获取布料列表（支持搜索过滤和分页，支持 name、purchase_channel、material_id、thickness_id、width、length 过滤）"""
    # 计算跳过的记录数
    skip = (page - 1) * limit
    
    # 直接查询数据
    from ..utils.query_helpers import filter_by_code_type, filter_by_code_ids
    query = db.query(Fabric)
    
    # 构建基础过滤条件
    filters = {}
    if name:
        filters["name"] = name
    if purchase_channel:
        filters["purchase_channel"] = purchase_channel
    if material_id:
        filters["material_id"] = material_id
    if thickness_id:
        filters["thickness_id"] = thickness_id
    if width:
        filters["width"] = width
    if length:
        filters["length"] = length
    
    # 处理通用查询参数（动态字段查询）
    if code_type and code_id:
        query = filter_by_code_type(query, Fabric, db, code_type, code_id, entity_type='fabric')
    
    # 处理颜色列表（多对多关系）
    if color_ids:
        query = filter_by_code_ids(query, Fabric, db, 'fabric_color', color_ids, entity_type='fabric')
    
    # 应用过滤条件
    for key, value in filters.items():
        if hasattr(Fabric, key):
            if isinstance(value, str):
                query = query.filter(getattr(Fabric, key).like(f"%{value}%"))
            else:
                query = query.filter(getattr(Fabric, key) == value)
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据并加载图片
    fabrics = query.offset(skip).limit(limit).all()
    
    # 为每个布料加载关联的图片信息
    for fabric in fabrics:
        fabric.images = db.query(Image).filter(
            Image.entity_type == "fabric",
            Image.entity_id == fabric.id
        ).all()
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    serialized_fabrics = serialize_list(fabrics, base_url)
    
    # 转换为标准分页格式
    return {
        "code": 200,
        "message": "",
        "data": {
            "items": serialized_fabrics,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }

@router.put("/{fabric_id}", response_model=ApiResponse)
def update_fabric(fabric_id: int, request: Request, fabric: FabricUpdate, db: Session = Depends(get_db)):
    """更新布料（包含编码和图片关联）"""
    db_fabric = db.query(Fabric).filter(Fabric.id == fabric_id).first()
    if not db_fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    
    # 提取关联字段
    material_id = getattr(fabric, 'material_id', None)
    thickness_id = getattr(fabric, 'thickness_id', None)
    color_ids = getattr(fabric, 'color_ids', None)
    image_ids = getattr(fabric, 'image_ids', None)
    
    # 更新基本字段
    update_dict = fabric.dict(exclude_unset=True, exclude={'material_id', 'thickness_id', 'color_ids', 'image_ids', 'images'})
    for key, value in update_dict.items():
        setattr(db_fabric, key, value)
    
    # 更新编码关联
    if material_id is not None:
        db_fabric.material_id = material_id
    if thickness_id is not None:
        db_fabric.thickness_id = thickness_id
    
    # 更新颜色多对多关联
    if color_ids is not None:
        from ..models import FabricColor
        # 删除现有关联
        db.query(FabricColor).filter(FabricColor.fabric_id == fabric_id).delete()
        # 添加新关联
        for color_id in color_ids:
            fabric_color = FabricColor(fabric_id=fabric_id, code_id=color_id)
            db.add(fabric_color)
    
    # 更新图片关联
    if image_ids is not None:
        # 更新现有图片的entity_id
        for image_ref in image_ids:
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = fabric_id
                db_image.entity_type = "fabric"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_fabric)
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    fabric_dict = serialize_model(db_fabric, base_url)
    
    return {
        "code": 200,
        "message": "Fabric updated successfully",
        "data": fabric_dict
    }

@router.get("/count", response_model=ApiResponse)
def get_fabrics_count(db: Session = Depends(get_db)):
    """获取布料总数"""
    count = db.query(Fabric).count()
    return {
        "code": 200,
        "message": "",
        "data": {
            "count": count
        }
    }

@router.get("/stats/all", response_model=ApiResponse)
def get_all_entities_stats(db: Session = Depends(get_db)):
    """获取所有实体统计信息"""
    from ..models import Pattern, Project, Item
    
    stats = {
        "fabrics": db.query(Fabric).count(),
        "patterns": db.query(Pattern).count(),
        "projects": db.query(Project).count(),
        "items": db.query(Item).count()
    }
    
    return {
        "code": 200,
        "message": "",
        "data": stats
    }

@router.delete("/{fabric_id}", response_model=ApiResponse)
def delete_fabric(fabric_id: int, db: Session = Depends(get_db)):
    """删除布料"""
    fabric = db.query(Fabric).filter(Fabric.id == fabric_id).first()
    if not fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    
    db.delete(fabric)
    db.commit()
    return {
        "code": 200,
        "message": "Fabric deleted successfully",
        "data": None
    }