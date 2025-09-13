"""测试 python-dotenv 集成."""

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


def test_dotenv_loading():
    """测试 python-dotenv 加载."""
    
    logger.info("测试 python-dotenv 环境变量加载")
    
    # 检查 .env 文件是否存在
    env_file = ".env"
    if not os.path.exists(env_file):
        logger.error(f"❌ .env 文件不存在: {env_file}")
        return False
    
    logger.info(f"✅ 找到 .env 文件: {env_file}")
    
    # 尝试加载 python-dotenv
    try:
        from dotenv import load_dotenv
        
        # 清除现有的环境变量（仅用于测试）
        test_key = 'PATENT_VIEW_API_KEY'
        original_value = os.environ.get(test_key)
        if test_key in os.environ:
            del os.environ[test_key]
        
        # 加载 .env 文件
        result = load_dotenv()
        logger.info(f"✅ python-dotenv 加载结果: {result}")
        
        # 检查环境变量是否正确加载
        loaded_value = os.getenv(test_key)
        if loaded_value:
            logger.info(f"✅ 成功加载 {test_key}: {loaded_value[:10]}...{loaded_value[-5:] if len(loaded_value) > 15 else loaded_value}")
            return True
        else:
            logger.error(f"❌ 未能加载 {test_key}")
            return False
            
    except ImportError:
        logger.error("❌ python-dotenv 未安装")
        return False
    except Exception as e:
        logger.error(f"❌ python-dotenv 加载失败: {str(e)}")
        return False


def test_config_with_dotenv():
    """测试配置类使用 python-dotenv."""
    
    logger.info("测试配置类使用 python-dotenv")
    
    try:
        from src.multi_agent_service.patent.config.patentsview_config import PatentsViewAPIConfig
        
        # 创建配置实例
        config = PatentsViewAPIConfig.from_env()
        
        logger.info(f"API 基础URL: {config.base_url}")
        logger.info(f"API 密钥: {'✅ 已配置' if config.api_key else '❌ 未配置'}")
        
        if config.api_key:
            logger.info(f"  密钥长度: {len(config.api_key)} 字符")
            logger.info(f"  密钥预览: {config.api_key[:10]}...{config.api_key[-5:] if len(config.api_key) > 15 else config.api_key}")
        
        logger.info(f"超时设置: {config.timeout}秒")
        logger.info(f"最大重试: {config.max_retries}次")
        logger.info(f"缓存启用: {config.enable_cache}")
        
        return config.api_key is not None
        
    except Exception as e:
        logger.error(f"❌ 配置测试失败: {str(e)}")
        return False


def test_service_with_dotenv():
    """测试服务类使用 python-dotenv."""
    
    logger.info("测试服务类使用 python-dotenv")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        # 创建服务实例
        service = PatentsViewService()
        
        logger.info(f"服务 API 密钥: {'✅ 已配置' if service.api_key else '❌ 未配置'}")
        
        if service.api_key:
            logger.info(f"  密钥长度: {len(service.api_key)} 字符")
            logger.info(f"  密钥预览: {service.api_key[:10]}...{service.api_key[-5:] if len(service.api_key) > 15 else service.api_key}")
        
        logger.info(f"服务基础URL: {service.base_url}")
        
        # 测试查询构建功能
        text_query = service.build_text_search_query(["test"])
        logger.info(f"查询构建测试: {text_query}")
        
        return service.api_key is not None
        
    except Exception as e:
        logger.error(f"❌ 服务测试失败: {str(e)}")
        return False


def test_agent_with_dotenv():
    """测试智能体使用 python-dotenv."""
    
    logger.info("测试智能体使用 python-dotenv")
    
    try:
        from src.multi_agent_service.patent.agents.patent_search import PatentsViewSearchAgent
        from src.multi_agent_service.models.config import AgentConfig, ModelConfig
        from src.multi_agent_service.models.enums import AgentType, ModelProvider
        
        # 创建模型配置
        llm_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test_key",
            base_url="https://api.openai.com/v1"
        )
        
        # 创建智能体配置
        config = AgentConfig(
            agent_id="test_patentsview_agent",
            agent_type=AgentType.PATENT_SEARCH,
            name="测试PatentsView智能体",
            description="用于测试的PatentsView智能体",
            capabilities=["专利搜索"],
            llm_config=llm_config,
            prompt_template="测试提示词模板",
            metadata={
                "patentsview_api": {
                    "base_url": "https://search.patentsview.org/api/v1",
                    "timeout": 30
                }
            }
        )
        
        # 创建模拟模型客户端
        class MockModelClient:
            def __init__(self, config):
                self.config = config
            
            async def generate_response(self, prompt, **kwargs):
                return "Mock response"
        
        model_client = MockModelClient(llm_config)
        
        # 创建智能体
        agent = PatentsViewSearchAgent(config, model_client)
        
        logger.info(f"智能体 API 密钥: {'✅ 已配置' if agent.api_config.get('api_key') else '❌ 未配置'}")
        
        if agent.api_config.get('api_key'):
            api_key = agent.api_config['api_key']
            logger.info(f"  密钥长度: {len(api_key)} 字符")
            logger.info(f"  密钥预览: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else api_key}")
        
        logger.info(f"智能体基础URL: {agent.api_config.get('base_url')}")
        
        return agent.api_config.get('api_key') is not None
        
    except Exception as e:
        logger.error(f"❌ 智能体测试失败: {str(e)}")
        return False


def test_env_file_content():
    """测试 .env 文件内容."""
    
    logger.info("测试 .env 文件内容")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        logger.error(f"❌ .env 文件不存在")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        logger.info(f"✅ .env 文件大小: {len(content)} 字符")
        
        # 检查关键的环境变量
        key_vars = ['PATENT_VIEW_API_KEY', 'OPENAI_API_KEY', 'BOCHA_AI_API_KEY']
        found_vars = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key = line.split('=')[0]
                if key in key_vars:
                    found_vars.append(key)
        
        logger.info(f"找到的关键变量: {found_vars}")
        
        return 'PATENT_VIEW_API_KEY' in found_vars
        
    except Exception as e:
        logger.error(f"❌ 读取 .env 文件失败: {str(e)}")
        return False


def main():
    """主测试函数."""
    
    logger.info("开始 python-dotenv 集成测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 测试 .env 文件内容
    result1 = test_env_file_content()
    test_results.append((".env 文件内容", result1))
    
    logger.info("=" * 60)
    
    # 测试 python-dotenv 加载
    result2 = test_dotenv_loading()
    test_results.append(("python-dotenv 加载", result2))
    
    logger.info("=" * 60)
    
    # 测试配置类
    result3 = test_config_with_dotenv()
    test_results.append(("配置类集成", result3))
    
    logger.info("=" * 60)
    
    # 测试服务类
    result4 = test_service_with_dotenv()
    test_results.append(("服务类集成", result4))
    
    logger.info("=" * 60)
    
    # 测试智能体
    result5 = test_agent_with_dotenv()
    test_results.append(("智能体集成", result5))
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("python-dotenv 集成测试结果:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"总计: {passed_count}/{len(test_results)} 个测试通过")
    
    if passed_count == len(test_results):
        logger.info("🎉 所有 python-dotenv 集成测试通过！")
        logger.info("✅ 环境变量加载正常")
        logger.info("✅ 所有组件都能正确读取 .env 文件")
    elif passed_count > 0:
        logger.warning("⚠️ 部分测试通过，请检查失败的组件")
    else:
        logger.error("❌ 所有测试失败，请检查 python-dotenv 安装和 .env 文件配置")
    
    return passed_count == len(test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)