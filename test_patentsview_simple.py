"""简单的 PatentsView API 测试."""

import asyncio
import aiohttp
import json
import logging
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_simple_get_request():
    """测试简单的 GET 请求."""
    
    logger.info("测试简单的 GET 请求（不使用 API 密钥）")
    
    # 尝试最简单的查询
    base_url = "https://search.patentsview.org/api/v1"
    endpoint = "/patent/"
    
    # 构建简单的查询参数
    params = {
        'q': json.dumps({"patent_date": {"_gte": "2024-01-01", "_lte": "2024-01-31"}}),
        'f': json.dumps(["patent_id", "patent_title"]),
        'o': json.dumps({"size": 3})
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 尝试 GET 请求
            logger.info("尝试 GET 请求...")
            async with session.get(f"{base_url}{endpoint}", params=params) as response:
                logger.info(f"GET 响应状态: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"GET 成功: 获取到数据 {len(str(data))} 字符")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"GET 失败: {error_text}")
    
    except Exception as e:
        logger.error(f"GET 请求异常: {str(e)}")
    
    return False


async def test_simple_post_request():
    """测试简单的 POST 请求."""
    
    logger.info("测试简单的 POST 请求（不使用 API 密钥）")
    
    base_url = "https://search.patentsview.org/api/v1"
    endpoint = "/patent/"
    
    # 构建 POST 请求体
    payload = {
        'q': {"patent_date": {"_gte": "2024-01-01", "_lte": "2024-01-31"}},
        'f': ["patent_id", "patent_title"],
        'o': {"size": 3}
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'PatentsViewTest/1.0'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 尝试 POST 请求
            logger.info("尝试 POST 请求...")
            async with session.post(f"{base_url}{endpoint}", json=payload, headers=headers) as response:
                logger.info(f"POST 响应状态: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"POST 成功: 获取到数据 {len(str(data))} 字符")
                    if 'patents' in data:
                        logger.info(f"专利数量: {len(data['patents'])}")
                        if data['patents']:
                            first_patent = data['patents'][0]
                            logger.info(f"第一个专利: {first_patent}")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"POST 失败: {error_text}")
    
    except Exception as e:
        logger.error(f"POST 请求异常: {str(e)}")
    
    return False


async def test_with_api_key():
    """测试使用 API 密钥的请求."""
    
    logger.info("测试使用 API 密钥的请求")
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    api_key = os.getenv('PATENT_VIEW_API_KEY')
    if not api_key:
        logger.warning("未找到 API 密钥，跳过此测试")
        return False
    
    logger.info(f"使用 API 密钥: {api_key[:10]}...{api_key[-5:]}")
    
    base_url = "https://search.patentsview.org/api/v1"
    endpoint = "/patent/"
    
    payload = {
        'q': {"patent_date": {"_gte": "2024-01-01", "_lte": "2024-01-31"}},
        'f': ["patent_id", "patent_title"],
        'o': {"size": 3}
    }
    
    # 尝试不同的认证方式
    auth_methods = [
        {'X-API-Key': api_key},
        {'Authorization': f'Bearer {api_key}'},
        {'Authorization': f'ApiKey {api_key}'},
        {'api_key': api_key}
    ]
    
    for i, auth_header in enumerate(auth_methods, 1):
        logger.info(f"尝试认证方式 {i}: {list(auth_header.keys())[0]}")
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PatentsViewTest/1.0',
            **auth_header
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}{endpoint}", json=payload, headers=headers) as response:
                    logger.info(f"  响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"  ✅ 成功: 获取到数据 {len(str(data))} 字符")
                        return True
                    else:
                        error_text = await response.text()
                        logger.info(f"  ❌ 失败: {error_text[:100]}...")
        
        except Exception as e:
            logger.info(f"  ❌ 异常: {str(e)}")
    
    return False


async def test_public_endpoints():
    """测试公开端点."""
    
    logger.info("测试可能的公开端点")
    
    base_url = "https://search.patentsview.org/api/v1"
    
    # 尝试一些可能不需要认证的端点
    endpoints = [
        "/cpc_class/",
        "/ipc/",
        "/uspc_mainclass/",
        "/wipo/"
    ]
    
    success_count = 0
    
    for endpoint in endpoints:
        logger.info(f"测试端点: {endpoint}")
        
        payload = {
            'q': {},
            'f': [],  # 使用默认字段
            'o': {"size": 3}
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PatentsViewTest/1.0'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}{endpoint}", json=payload, headers=headers) as response:
                    logger.info(f"  响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"  ✅ 成功: 获取到数据 {len(str(data))} 字符")
                        success_count += 1
                    else:
                        error_text = await response.text()
                        logger.info(f"  ❌ 失败: {error_text[:100]}...")
        
        except Exception as e:
            logger.info(f"  ❌ 异常: {str(e)}")
    
    return success_count > 0


async def main():
    """主测试函数."""
    
    logger.info("开始 PatentsView API 简单测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 测试简单 GET 请求
    result1 = await test_simple_get_request()
    test_results.append(("简单 GET 请求", result1))
    
    logger.info("=" * 60)
    
    # 测试简单 POST 请求
    result2 = await test_simple_post_request()
    test_results.append(("简单 POST 请求", result2))
    
    logger.info("=" * 60)
    
    # 测试使用 API 密钥
    result3 = await test_with_api_key()
    test_results.append(("API 密钥认证", result3))
    
    logger.info("=" * 60)
    
    # 测试公开端点
    result4 = await test_public_endpoints()
    test_results.append(("公开端点测试", result4))
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"总计: {passed_count}/{len(test_results)} 个测试通过")
    
    if passed_count > 0:
        logger.info("🎉 至少有一种方式可以访问 PatentsView API！")
    else:
        logger.error("❌ 所有访问方式都失败了。")
        logger.error("可能的原因:")
        logger.error("1. API 服务暂时不可用")
        logger.error("2. 需要不同的认证方式")
        logger.error("3. API 密钥无效")
        logger.error("4. 网络连接问题")
    
    return passed_count > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)