from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Project, Image
from ..schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ApiResponse
from ..utils.pagination import Pagination
from ..utils.query_helpers import serialize_model, serialize_list
from ..config import settings

router = APIRouter()

@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_project(request: Request, project: ProjectCreate, db: Session = Depends(get_db)):
    """创建作品（包含编码和图片关联）"""
    # 提取关联字段
    pattern_id = project.pattern_id
    type_id = project.type_id
    fabric_ids = project.fabric_ids or []
    technique_ids = project.technique_ids or []
    image_ids = project.image_ids or []
    
    # 创建作品主体（排除关联字段）
    project_dict = project.dict(exclude={'pattern_id', 'type_id', 'fabric_ids', 'technique_ids', 'image_ids', 'images'})
    db_project = Project(**project_dict)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # 处理编码关联
    if pattern_id:
        db_project.pattern_id = pattern_id
    if type_id:
        db_project.type_id = type_id
    
    # 处理布料多对多关联
    if fabric_ids:
        from ..models import ProjectFabric
        for fabric_id in fabric_ids:
            project_fabric = ProjectFabric(project_id=db_project.id, fabric_id=fabric_id)
            db.add(project_fabric)
    
    # 处理工艺多对多关联
    if technique_ids:
        from ..models import ProjectTechnique
        for technique_id in technique_ids:
            project_technique = ProjectTechnique(project_id=db_project.id, code_id=technique_id)
            db.add(project_technique)
    
    # 处理图片关联
    if image_ids:
        for image_ref in image_ids:
            # 更新图片的entity_id为新创建的作品ID
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = db_project.id
                db_image.entity_type = "project"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_project)
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    project_dict = serialize_model(db_project, base_url)
    
    return {
        "code": 201,
        "message": "Project created successfully",
        "data": project_dict
    }

@router.get("/{project_id}", response_model=ApiResponse)
def get_project(project_id: int, request: Request, db: Session = Depends(get_db)):
    """获取作品详情（包含关联的编码和图片信息）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 加载关联的图片信息
    project.images = db.query(Image).filter(
        Image.entity_type == "project",
        Image.entity_id == project_id
    ).all()
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    project_dict = serialize_model(project, base_url)
    
    return {
        "code": 200,
        "message": "",
        "data": project_dict
    }

@router.get("", response_model=ApiResponse)
def list_projects(
    request: Request,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    title: Optional[str] = Query(None, description="作品标题"),
    pattern_id: Optional[int] = Query(None, description="纸样 ID"),
    type_id: Optional[int] = Query(None, description="类型 ID"),
    fabric_ids: Optional[List[int]] = Query(None, description="布料 ID 列表（支持多个）"),
    technique_ids: Optional[List[int]] = Query(None, description="工艺 ID 列表（支持多个）"),
    # 通用查询参数
    code_type: Optional[str] = Query(None, description="编码类型（pattern/type/fabric/technique 等）"),
    code_id: Optional[int] = Query(None, description="编码 ID，与 code_type 配合使用"),
    db: Session = Depends(get_db)
):
    """获取作品列表（支持搜索过滤和分页）"""
    # 计算跳过的记录数
    skip = (page - 1) * limit
    
    # 直接查询数据
    from ..utils.query_helpers import filter_by_code_type, filter_by_code_ids
    query = db.query(Project)
    
    # 构建基础过滤条件
    filters = {}
    if title:
        filters["title"] = title
    if pattern_id:
        filters["pattern_id"] = pattern_id
    if type_id:
        filters["type_id"] = type_id
    
    # 处理通用查询参数（动态字段查询）
    if code_type and code_id:
        query = filter_by_code_type(query, Project, db, code_type, code_id, entity_type='project')
    
    # 处理多对多关系列表
    if fabric_ids:
        query = filter_by_code_ids(query, Project, db, 'fabric', fabric_ids, entity_type='project')
    if technique_ids:
        query = filter_by_code_ids(query, Project, db, 'technique', technique_ids, entity_type='project')
    
    # 应用基础过滤条件
    for key, value in filters.items():
        if hasattr(Project, key):
            if isinstance(value, str):
                query = query.filter(getattr(Project, key).like(f"%{value}%"))
            else:
                query = query.filter(getattr(Project, key) == value)
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据并加载图片
    projects = query.offset(skip).limit(limit).all()
    
    # 为每个作品加载关联的图片信息
    for project in projects:
        project.images = db.query(Image).filter(
            Image.entity_type == "project",
            Image.entity_id == project.id
        ).all()
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    serialized_projects = serialize_list(projects, base_url)
    
    # 转换为标准分页格式
    return {
        "code": 200,
        "message": "",
        "data": {
            "items": serialized_projects,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    }

@router.put("/{project_id}", response_model=ApiResponse)
def update_project(project_id: int, request: Request, project: ProjectUpdate, db: Session = Depends(get_db)):
    """更新作品（包含编码和图片关联）"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 提取关联字段
    pattern_id = getattr(project, 'pattern_id', None)
    type_id = getattr(project, 'type_id', None)
    fabric_ids = getattr(project, 'fabric_ids', None)
    technique_ids = getattr(project, 'technique_ids', None)
    image_ids = getattr(project, 'image_ids', None)
    
    # 更新基本字段
    update_dict = project.dict(exclude_unset=True, exclude={'pattern_id', 'type_id', 'fabric_ids', 'technique_ids', 'image_ids', 'images'})
    for key, value in update_dict.items():
        setattr(db_project, key, value)
    
    # 更新编码关联
    if pattern_id is not None:
        db_project.pattern_id = pattern_id
    if type_id is not None:
        db_project.type_id = type_id
    
    # 更新布料多对多关联
    if fabric_ids is not None:
        from ..models import ProjectFabric
        # 删除现有关联
        db.query(ProjectFabric).filter(ProjectFabric.project_id == project_id).delete()
        # 添加新关联
        for fabric_id in fabric_ids:
            project_fabric = ProjectFabric(project_id=project_id, fabric_id=fabric_id)
            db.add(project_fabric)
    
    # 更新工艺多对多关联
    if technique_ids is not None:
        from ..models import ProjectTechnique
        # 删除现有关联
        db.query(ProjectTechnique).filter(ProjectTechnique.project_id == project_id).delete()
        # 添加新关联
        for technique_id in technique_ids:
            project_technique = ProjectTechnique(project_id=project_id, code_id=technique_id)
            db.add(project_technique)
    
    # 更新图片关联
    if image_ids is not None:
        # 更新现有图片的entity_id
        for image_ref in image_ids:
            db_image = db.query(Image).filter(Image.id == image_ref.id).first()
            if db_image:
                db_image.entity_id = project_id
                db_image.entity_type = "project"
                # 更新图片的其他属性
                if image_ref.image_type:
                    db_image.image_type = image_ref.image_type
                if image_ref.sort_order is not None:
                    db_image.sort_order = image_ref.sort_order
                if image_ref.description:
                    db_image.description = image_ref.description
    
    db.commit()
    db.refresh(db_project)
    
    # 获取基础URL
    base_url = str(request.base_url).rstrip('/')
    
    # 序列化为字典格式
    project_dict = serialize_model(db_project, base_url)
    
    return {
        "code": 200,
        "message": "Project updated successfully",
        "data": project_dict
    }

@router.get("/count", response_model=ApiResponse)
def get_projects_count(db: Session = Depends(get_db)):
    """获取作品总数"""
    count = db.query(Project).count()
    return {
        "code": 200,
        "message": "",
        "data": {
            "count": count
        }
    }

@router.delete("/{project_id}", response_model=ApiResponse)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除作品"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {
        "code": 200,
        "message": "Project deleted successfully",
        "data": None
    }