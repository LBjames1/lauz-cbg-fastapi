from minio import Minio
from minio.error import S3Error
from .config import settings

def init_minio_client():
    """初始化MinIO客户端"""
    try:
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # 检查存储桶是否存在，不存在则创建
        if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
            client.make_bucket(settings.MINIO_BUCKET_NAME)
            print(f"Bucket '{settings.MINIO_BUCKET_NAME}' created successfully")
        
        return client
    except S3Error as e:
        print(f"MinIO connection error: {e}")
        raise

def upload_file(client, bucket_name, object_name, file_data, content_type="application/octet-stream"):
    """上传文件到MinIO"""
    try:
        from io import BytesIO
        # 如果file_data是bytes类型，包装为BytesIO
        if isinstance(file_data, bytes):
            file_obj = BytesIO(file_data)
        else:
            file_obj = file_data
            
        result = client.put_object(
            bucket_name,
            object_name,
            file_obj,
            len(file_data),
            content_type=content_type
        )
        return f"http://{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"
    except S3Error as e:
        raise Exception(f"Failed to upload file: {e}")

def get_presigned_url(client, bucket_name, object_name, expires=604800):
    """获取预签名URL"""
    try:
        return client.presigned_get_object(bucket_name, object_name, expires=expires)
    except S3Error as e:
        raise Exception(f"Failed to get presigned URL: {e}")