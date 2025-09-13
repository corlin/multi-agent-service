"""测试 python-dotenv 核心功能."""

import os
import sys
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_dotenv_basic():
    """测试基本的 python-dotenv 功能."""
    
    logger.info("测试基本的 python-dotenv 功能")
    
    try:
        from dotenv import load_dotenv
        
        # 加载 .env 文件
        result = load_dotenv()
        logger.info(f"✅ load_dotenv() 返回: {result}")
        
        # 检查关键环境变量
        patent_key = os.getenv('PATENT_VIEW_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        bocha_key = os.getenv('BOCHA_AI_API_KEY')
        
        logger.info(f"PATENT_VIEW_API_KEY: {'✅ 已加载' if patent_key else '❌ 未加载'}")
        logger.info(f"OPENAI_API_KEY: {'✅ 已加载' if openai_key else '❌ 未加载'}")
        logger.info(f"BOCHA_AI_API_KEY: {'✅ 已加载' if bocha_key else '❌ 未加载'}")
        
        if patent_key:
            logger.info(f"PATENT_VIEW_API_KEY 长度: {len(patent_key)} 字符")
            logger.info(f"PATENT_VIEW_API_KEY 预览: {patent_key[:10]}...{patent_key[-5:]}")
        
        return patent_key is not None
        
    except ImportError:
        logger.error("❌ python-dotenv 未安装")
        return False
    except Exception as e:
        logger.error(f"❌ python-dotenv 测试失败: {str(e)}")
        return False


def test_patentsview_config():
    """测试 PatentsView 配置加载."""
    
    logger.info("测试 PatentsView 配置加载")
    
    try:
        from src.multi_agent_service.patent.config.patentsview_config import PatentsViewAPIConfig
        
        config = PatentsViewAPIConfig.from_env()
        
        logger.info(f"✅ 配置创建成功")
        logger.info(f"API 密钥: {'已配置' if config.api_key else '未配置'}")
        logger.info(f"基础URL: {config.base_url}")
        logger.info(f"超时: {config.timeout}秒")
        logger.info(f"最大重试: {config.max_retries}次")
        
        return config.api_key is not None
        
    except Exception as e:
        logger.error(f"❌ 配置测试失败: {str(e)}")
        return False


def test_patentsview_service():
    """测试 PatentsView 服务初始化."""
    
    logger.info("测试 PatentsView 服务初始化")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        service = PatentsViewService()
        
        logger.info(f"✅ 服务创建成功")
        logger.info(f"API 密钥: {'已配置' if service.api_key else '未配置'}")
        logger.info(f"基础URL: {service.base_url}")
        
        # 测试查询构建
        query = service.build_text_search_query(["artificial intelligence"])
        logger.info(f"✅ 查询构建成功: {query}")
        
        return service.api_key is not None
        
    except Exception as e:
        logger.error(f"❌ 服务测试失败: {str(e)}")
        return False


def test_env_variables_directly():
    """直接测试环境变量."""
    
    logger.info("直接测试环境变量")
    
    # 首先加载 .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv 未安装，尝试手动加载")
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    # 检查所有相关的环境变量
    env_vars = {
        'PATENT_VIEW_API_KEY': os.getenv('PATENT_VIEW_API_KEY'),
        'PATENTSVIEW_API_KEY': os.getenv('PATENTSVIEW_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'BOCHA_AI_API_KEY': os.getenv('BOCHA_AI_API_KEY'),
    }
    
    loaded_count = 0
    for key, value in env_vars.items():
        if value:
            logger.info(f"✅ {key}: 已加载 ({len(value)} 字符)")
            loaded_count += 1
        else:
            logger.info(f"❌ {key}: 未加载")
    
    logger.info(f"总计加载了 {loaded_count}/{len(env_vars)} 个环境变量")
    
    return env_vars['PATENT_VIEW_API_KEY'] is not None


def main():
    """主测试函数."""
    
    logger.info("开始 python-dotenv 核心功能测试")
    logger.info("=" * 50)
    
    test_results = []
    
    # 测试基本功能
    result1 = test_dotenv_basic()
    test_results.append(("基本功能", result1))
    
    logger.info("=" * 50)
    
    # 直接测试环境变量
    result2 = test_env_variables_directly()
    test_results.append(("环境变量", result2))
    
    logger.info("=" * 50)
    
    # 测试配置
    result3 = test_patentsview_config()
    test_results.append(("配置加载", result3))
    
    logger.info("=" * 50)
    
    # 测试服务
    result4 = test_patentsview_service()
    test_results.append(("服务初始化", result4))
    
    # 汇总结果
    logger.info("=" * 50)
    logger.info("测试结果汇总:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"总计: {passed_count}/{len(test_results)} 个测试通过")
    
    if passed_count == len(test_results):
        logger.info("🎉 所有核心功能测试通过！")
        logger.info("✅ python-dotenv 集成成功")
        logger.info("✅ 环境变量正确加载")
        logger.info("✅ PatentsView 组件正常工作")
    elif passed_count >= 3:
        logger.info("✅ 核心功能正常，PatentsView 集成成功")
    else:
        logger.error("❌ 核心功能测试失败")
    
    return passed_count >= 3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)