from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Image
from ..schemas import ImageCreate, ImageResponse, ApiResponse, ImageBase
from ..minio_client import init_minio_client, upload_file, get_presigned_url, get_image_data
from ..config import settings
import uuid

router = APIRouter()

# 初始化MinIO客户端
minio_client = init_minio_client()

@router.get("/health", response_model=ApiResponse)
def check_upload_health():
    """检查上传服务健康状态"""
    try:
        # 检查 MinIO 连接
        bucket_exists = minio_client.bucket_exists(settings.MINIO_BUCKET_NAME)
        return {
            "code": 200,
            "message": "Upload service is healthy",
            "data": {
                "minio_connected": True,
                "bucket_exists": bucket_exists,
                "bucket_name": settings.MINIO_BUCKET_NAME,
                "minio_endpoint": settings.MINIO_ENDPOINT
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": "Upload service is unhealthy",
            "data": {
                "minio_connected": False,
                "error": str(e)
            }
        }

@router.post("/images", response_model=ApiResponse)
async def upload_images(
    entity_type: Optional[str] = Form(None),  # 改为可选参数
    entity_id: Optional[int] = Form(None),  # 改为可选参数
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """上传图片（支持临时上传，无需立即关联实体）"""
    uploaded_images = []
    
    for file in files:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # 生成唯一文件名
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # 上传到MinIO
        try:
            # 读取文件内容
            file_content = await file.read()
            file_url = upload_file(minio_client, settings.MINIO_BUCKET_NAME, unique_filename, file_content, file.content_type)
            
            # 保存到数据库 - entity_type 和 entity_id 都是可选的
            image_data = {
                "image_url": file_url,
                "image_type": "normal"
            }
            # 只有当提供了这些字段时才设置
            if entity_type is not None:
                image_data["entity_type"] = entity_type
            if entity_id is not None:
                image_data["entity_id"] = entity_id
            
            db_image = Image(**image_data)
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            
            # 转换为字典格式用于响应
            image_dict = {
                "id": db_image.id,
                "entity_type": db_image.entity_type,
                "entity_id": db_image.entity_id,
                "image_url": db_image.image_url,
                "image_type": db_image.image_type,
                "sort_order": db_image.sort_order,
                "description": db_image.description,
                "created_at": db_image.created_at,
                "updated_at": db_image.updated_at
            }
            uploaded_images.append(image_dict)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    return {
        "code": 200,
        "message": f"Successfully uploaded {len(uploaded_images)} images",
        "data": uploaded_images
    }

@router.get("/images/{image_id}/preview", response_model=ApiResponse)
async def preview_image(image_id: int, db: Session = Depends(get_db)):
    """预览图片（基于图片ID）"""
    # 从数据库获取图片记录
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # 从图片URL中提取文件名
        # image_url 格式: http://endpoint/bucket/filename
        filename = image.image_url.split("/")[-1]
        
        # 获取预签名 URL
        presigned_url = get_presigned_url(minio_client, settings.MINIO_BUCKET_NAME, filename)
        
        return {
            "code": 200,
            "message": "",
            "data": {
                "url": presigned_url,
                "filename": filename,
                "entity_type": image.entity_type,
                "entity_id": image.entity_id
            }
        }
    except Exception as e:
        # 提供更详细的错误信息
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate preview URL: {str(e)}. Image URL: {image.image_url}, Filename: {filename if 'filename' in locals() else 'N/A'}"
        )

@router.get("/images/{image_id}/download", response_model=ApiResponse)
async def download_file(image_id: int, db: Session = Depends(get_db)):
    """下载文件（基于图片ID）"""
    # 从数据库获取图片记录
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # 从图片URL中提取文件名
        # image_url 格式: http://endpoint/bucket/filename
        filename = image.image_url.split("/")[-1]
        
        # 获取预签名 URL
        presigned_url = get_presigned_url(minio_client, settings.MINIO_BUCKET_NAME, filename)
        
        return {
            "code": 200,
            "message": "",
            "data": {
                "download_url": presigned_url,
                "filename": filename,
                "entity_type": image.entity_type,
                "entity_id": image.entity_id
            }
        }
    except Exception as e:
        # 提供更详细的错误信息
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate download URL: {str(e)}. Image URL: {image.image_url}, Filename: {filename if 'filename' in locals() else 'N/A'}"
        )

@router.get("/images/{image_id}/view")
async def view_image(image_id: int, db: Session = Depends(get_db)):
    """直接查看图片（返回图片二进制数据，适用于无法直接访问MinIO的场景）"""
    # 从数据库获取图片记录
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # 从图片URL中提取文件名
        filename = image.image_url.split("/")[-1]
        
        # 从 MinIO 获取图片二进制数据
        image_data = get_image_data(minio_client, settings.MINIO_BUCKET_NAME, filename)
        
        # 根据文件扩展名确定内容类型
        content_type = "image/jpeg"  # 默认
        if filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        return Response(content=image_data, media_type=content_type)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve image: {str(e)}"
        )

@router.put("/images/{image_id}/associate", response_model=ApiResponse)
def associate_image(
    image_id: int,
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """关联图片到具体实体"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # 更新关联信息
    image.entity_type = entity_type
    image.entity_id = entity_id
    db.commit()
    db.refresh(image)
    
    # 转换为字典格式用于响应
    image_dict = {
        "id": image.id,
        "entity_type": image.entity_type,
        "entity_id": image.entity_id,
        "image_url": image.image_url,
        "image_type": image.image_type,
        "sort_order": image.sort_order,
        "description": image.description,
        "created_at": image.created_at,
        "updated_at": image.updated_at
    }
    
    return {
        "code": 200,
        "message": "Image associated successfully",
        "data": image_dict
    }

@router.delete("/images/{image_id}", response_model=ApiResponse)
def delete_image(image_id: int, db: Session = Depends(get_db)):
    """删除图片"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # 从MinIO删除文件
        filename = image.image_url.split("/")[-1]
        minio_client.remove_object(settings.MINIO_BUCKET_NAME, filename)
        
        # 从数据库删除记录
        db.delete(image)
        db.commit()
        
        return {
            "code": 200,
            "message": "Image deleted successfully",
            "data": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")