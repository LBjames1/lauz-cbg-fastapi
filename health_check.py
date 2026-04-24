import requests
import os
from dotenv import load_dotenv

def check_health():
    """健康检查脚本"""
    # 加载环境变量
    load_dotenv()
    
    print("开始健康检查...")
    
    # 检查API服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常")
        else:
            print(f"❌ API服务异常: {response.status_code}")
    except Exception as e:
        print(f"❌ API服务连接失败: {e}")

if __name__ == "__main__":
    check_health()