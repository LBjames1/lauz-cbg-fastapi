import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:Arkj1234!@192.168.3.121:3308/cbg_db"
    
    # MinIO 配置
    MINIO_ENDPOINT: str = "172.16.30.115:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "Arkj1234!"
    MINIO_BUCKET_NAME: str = "cbg-bucket"
    MINIO_SECURE: bool = False
    
    # JWT 配置
    SECRET_KEY: str = "cbg_fastapi_secret_key_20260228"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

# 创建配置实例
settings = Settings()