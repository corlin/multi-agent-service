#!/usr/bin/env python3
"""测试QWEN API密钥和连接."""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_qwen_api():
    """测试QWEN API连接."""
    
    # 获取配置
    api_key = os.getenv("QWEN_API_KEY")
    api_url = os.getenv("QWEN_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    print(f"API Key: {api_key[:10]}..." if api_key else "No API Key")
    print(f"API URL: {api_url}")
    
    if not api_key:
        print("❌ 没有找到QWEN_API_KEY环境变量")
        return False
    
    # 准备请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "multi-agent-service/1.0.0"
    }
    
    data = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "user", "content": "ping"}
        ],
        "max_tokens": 1,
        "temperature": 0.0
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🔄 发送测试请求...")
            
            response = await client.post(
                f"{api_url}/chat/completions",
                json=data,
                headers=headers
            )
            
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API调用成功!")
                print(f"📝 响应内容: {result}")
                return True
            else:
                print(f"❌ API调用失败: {response.status_code}")
                print(f"📄 错误内容: {response.text}")
                
                # 检查常见错误
                if response.status_code == 401:
                    print("🔍 401错误可能原因:")
                    print("   1. API密钥无效或过期")
                    print("   2. API密钥格式错误")
                    print("   3. 账户余额不足")
                    print("   4. API密钥权限不足")
                
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_qwen_api())