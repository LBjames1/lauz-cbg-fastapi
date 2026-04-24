from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Fabric, Image
from ..schemas import FabricCreate, FabricUpdate, FabricResponse, ApiResponse
from ..utils.pagination import Pagination
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
    
    result = {
        "items": fabrics,
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
def create_fabric(fabric: FabricCreate, db: Session = Depends(get_db)):
    """创建布料（包含编码和图片关联）"""
    # 提取关联字段
    material_id = fabric.material_id
    thickness_id = fabric.thickness_id
    color_ids = fabric.color_ids or []
    image_ids = fabric.image_ids or []
    
    # 创建布料主体（排除关联字段）
    fabric_dict = fabric.dict(exclude={'material_id', 'thickness_id', 'color_ids', 'images'})
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
    
    return {
        "code": 201,
        "message": "Fabric created successfully",
        "data": db_fabric
    }

@router.get("/{fabric_id}", response_model=ApiResponse)
def get_fabric(fabric_id: int, db: Session = Depends(get_db)):
    """获取布料详情（包含关联的编码和图片信息）"""
    fabric = db.query(Fabric).filter(Fabric.id == fabric_id).first()
    if not fabric:
        raise HTTPException(status_code=404, detail="Fabric not found")
    
    # 加载关联的图片信息
    fabric.images = db.query(Image).filter(
        Image.entity_type == "fabric",
        Image.entity_id == fabric_id
    ).all()
    
    return {
        "code": 200,
        "message": "",
        "data": fabric
    }

@router.get("", response_model=ApiResponse)
def list_fabrics(
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
        if code_type == "material":
            filters["material_id"] = code_id
        elif code_type == "thickness":
            filters["thickness_id"] = code_id
        elif code_type == "color":
            # 颜色是多对多关系，需要特殊处理
            from ..models import FabricColor
            fabric_ids = db.query(FabricColor.fabric_id).filter(
                FabricColor.code_id == code_id
            ).all()
            fabric_ids = [fid[0] for fid in fabric_ids]
            if fabric_ids:
                query = query.filter(Fabric.id.in_(fabric_ids))
            else:
                # 如果没有匹配的布料，返回空结果
                query = query.filter(Fabric.id == -1)
    
    # 处理颜色列表（多对多关系）
    if color_ids:
        from ..models import FabricColor
        fabric_ids = db.query(FabricColor.fabric_id).filter(
            FabricColor.code_id.in_(color_ids)
        ).all()
        fabric_ids = [fid[0] for fid in fabric_ids]
        if fabric_ids:
            query = query.filter(Fabric.id.in_(fabric_ids))
        else:
            query = query.filter(Fabric.id == -1)
    
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
    
    # 转换为标准分页格式
    return {
        "code": 200,
        "message": "",
        "data": {
            "items": fabrics,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }

@router.put("/{fabric_id}", response_model=ApiResponse)
def update_fabric(fabric_id: int, fabric: FabricUpdate, db: Session = Depends(get_db)):
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
    update_dict = fabric.dict(exclude_unset=True, exclude={'material_id', 'thickness_id', 'color_ids', 'images'})
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
    return {
        "code": 200,
        "message": "Fabric updated successfully",
        "data": db_fabric
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