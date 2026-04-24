from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Image
from ..schemas import ImageCreate, ImageResponse, ApiResponse
from ..minio_client import init_minio_client, upload_file, get_presigned_url
from ..config import settings
import uuid

router = APIRouter()

# 初始化MinIO客户端
minio_client = init_minio_client()

@router.post("/images", response_model=ApiResponse)
async def upload_images(
    entity_type: str = Form(...),
    entity_id: Optional[int] = Form(None),  # 改为可选参数
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """上传图片"""
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
            
            # 保存到数据库
            db_image = Image(
                entity_type=entity_type,
                entity_id=entity_id or 0,  # 如果没有entity_id，暂时设为0
                image_url=file_url,
                image_type="normal"
            )
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            uploaded_images.append(db_image)
            
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
        filename = image.image_url.split("/")[-1]
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
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")

@router.get("/images/{image_id}/download", response_model=ApiResponse)
async def download_file(image_id: int, db: Session = Depends(get_db)):
    """下载文件（基于图片ID）"""
    # 从数据库获取图片记录
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # 从图片URL中提取文件名
        filename = image.image_url.split("/")[-1]
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
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

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
    
    return {
        "code": 200,
        "message": "Image associated successfully",
        "data": image
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