import os
import uuid
from PIL import Image
from io import BytesIO
from .. import minio_client

def generate_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    ext = os.path.splitext(original_filename)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    return filename

def resize_image(image_data: bytes, max_size: tuple = (800, 800)) -> bytes:
    """压缩图片"""
    try:
        image = Image.open(BytesIO(image_data))
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 保存为JPEG格式，质量85%
        img_byte_arr = BytesIO()
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
        
        return img_byte_arr.getvalue()
    except Exception as e:
        raise Exception(f"Image resize failed: {e}")

def upload_image_to_minio(client, file_data: bytes, original_filename: str, bucket_name: str) -> str:
    """上传图片到MinIO并返回URL"""
    try:
        # 生成唯一文件名
        filename = generate_filename(original_filename)
        
        # 压缩图片
        resized_data = resize_image(file_data)
        
        # 上传到MinIO
        url = minio_client.upload_file(
            client, 
            bucket_name, 
            filename, 
            resized_data,
            content_type="image/jpeg"
        )
        
        return url
    except Exception as e:
        raise Exception(f"Upload image failed: {e}")

def init_minio_client():
    """初始化MinIO客户端（供main.py调用）"""
    return minio_client.init_minio_client()