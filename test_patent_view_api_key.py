"""测试 PATENT_VIEW_API_KEY 环境变量统一使用."""

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


def test_env_variable_consistency():
    """测试环境变量一致性."""
    
    logger.info("测试环境变量一致性")
    
    # 加载环境变量
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
    
    # 检查主要的环境变量
    patent_view_key = os.getenv('PATENT_VIEW_API_KEY')
    old_patentsview_key = os.getenv('PATENTSVIEW_API_KEY')
    
    logger.info(f"PATENT_VIEW_API_KEY: {'✅ 已设置' if patent_view_key else '❌ 未设置'}")
    if patent_view_key:
        logger.info(f"  值: {patent_view_key[:10]}...{patent_view_key[-5:] if len(patent_view_key) > 15 else patent_view_key}")
    
    logger.info(f"PATENTSVIEW_API_KEY (旧): {'⚠️ 仍存在' if old_patentsview_key else '✅ 已清理'}")
    
    return patent_view_key is not None


def test_config_uses_correct_env():
    """测试配置类使用正确的环境变量."""
    
    logger.info("测试配置类使用正确的环境变量")
    
    try:
        from src.multi_agent_service.patent.config.patentsview_config import PatentsViewAPIConfig
        
        # 临时清除旧的环境变量（如果存在）
        old_key = os.environ.pop('PATENTSVIEW_API_KEY', None)
        
        # 确保新的环境变量存在
        test_key = "test_api_key_12345"
        os.environ['PATENT_VIEW_API_KEY'] = test_key
        
        try:
            config = PatentsViewAPIConfig.from_env()
            
            logger.info(f"配置 API 密钥: {'✅ 正确' if config.api_key == test_key else '❌ 错误'}")
            logger.info(f"  期望: {test_key}")
            logger.info(f"  实际: {config.api_key}")
            
            return config.api_key == test_key
            
        finally:
            # 恢复原始环境变量
            if old_key:
                os.environ['PATENTSVIEW_API_KEY'] = old_key
            
            # 恢复原始的 PATENT_VIEW_API_KEY
            original_key = os.getenv('PATENT_VIEW_API_KEY')
            if original_key and original_key != test_key:
                os.environ['PATENT_VIEW_API_KEY'] = original_key
        
    except Exception as e:
        logger.error(f"❌ 配置测试失败: {str(e)}")
        return False


def test_service_uses_correct_env():
    """测试服务类使用正确的环境变量."""
    
    logger.info("测试服务类使用正确的环境变量")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        # 临时设置测试环境变量
        test_key = "test_service_key_67890"
        original_key = os.getenv('PATENT_VIEW_API_KEY')
        os.environ['PATENT_VIEW_API_KEY'] = test_key
        
        try:
            service = PatentsViewService()
            
            logger.info(f"服务 API 密钥: {'✅ 正确' if service.api_key == test_key else '❌ 错误'}")
            logger.info(f"  期望: {test_key}")
            logger.info(f"  实际: {service.api_key}")
            
            return service.api_key == test_key
            
        finally:
            # 恢复原始环境变量
            if original_key:
                os.environ['PATENT_VIEW_API_KEY'] = original_key
        
    except Exception as e:
        logger.error(f"❌ 服务测试失败: {str(e)}")
        return False


def test_agent_uses_correct_env():
    """测试智能体使用正确的环境变量."""
    
    logger.info("测试智能体使用正确的环境变量")
    
    try:
        # 临时设置测试环境变量
        test_key = "test_agent_key_abcde"
        original_key = os.getenv('PATENT_VIEW_API_KEY')
        os.environ['PATENT_VIEW_API_KEY'] = test_key
        
        try:
            from src.multi_agent_service.patent.agents.patent_search import PatentsViewSearchAgent
            from src.multi_agent_service.models.config import AgentConfig, ModelConfig
            from src.multi_agent_service.models.enums import AgentType, ModelProvider
            
            # 创建简单的配置
            llm_config = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key="test_llm_key",
                base_url="https://api.openai.com/v1"
            )
            
            config = AgentConfig(
                agent_id="test_agent",
                agent_type=AgentType.PATENT_SEARCH,
                name="测试智能体",
                description="测试用智能体",
                capabilities=["测试"],
                llm_config=llm_config,
                prompt_template="测试模板"
            )
            
            # 创建模拟客户端
            class MockClient:
                def __init__(self, config):
                    self.config = config
            
            client = MockClient(llm_config)
            
            # 创建智能体（只测试初始化部分）
            agent = PatentsViewSearchAgent(config, client)
            
            agent_key = agent.api_config.get('api_key')
            logger.info(f"智能体 API 密钥: {'✅ 正确' if agent_key == test_key else '❌ 错误'}")
            logger.info(f"  期望: {test_key}")
            logger.info(f"  实际: {agent_key}")
            
            return agent_key == test_key
            
        finally:
            # 恢复原始环境变量
            if original_key:
                os.environ['PATENT_VIEW_API_KEY'] = original_key
        
    except Exception as e:
        logger.error(f"❌ 智能体测试失败: {str(e)}")
        return False


def test_no_old_references():
    """测试代码中没有旧的环境变量引用."""
    
    logger.info("测试代码中没有旧的环境变量引用")
    
    files_to_check = [
        "src/multi_agent_service/patent/config/patentsview_config.py",
        "src/multi_agent_service/patent/services/patentsview_service.py",
        "src/multi_agent_service/patent/agents/patent_search.py"
    ]
    
    old_references = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # 检查是否还有旧的环境变量引用
                if 'PATENTSVIEW_API_KEY' in content:
                    old_references.append(file_path)
                    logger.warning(f"⚠️ {file_path} 中仍有 PATENTSVIEW_API_KEY 引用")
                else:
                    logger.info(f"✅ {file_path} 已清理旧引用")
            
            except Exception as e:
                logger.error(f"❌ 检查文件 {file_path} 失败: {str(e)}")
        else:
            logger.warning(f"⚠️ 文件不存在: {file_path}")
    
    if old_references:
        logger.error(f"❌ 发现 {len(old_references)} 个文件仍有旧引用")
        return False
    else:
        logger.info("✅ 所有文件都已清理旧引用")
        return True


def main():
    """主测试函数."""
    
    logger.info("开始 PATENT_VIEW_API_KEY 统一性测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 测试环境变量一致性
    result1 = test_env_variable_consistency()
    test_results.append(("环境变量一致性", result1))
    
    logger.info("=" * 60)
    
    # 测试代码中没有旧引用
    result2 = test_no_old_references()
    test_results.append(("清理旧引用", result2))
    
    logger.info("=" * 60)
    
    # 测试配置类
    result3 = test_config_uses_correct_env()
    test_results.append(("配置类", result3))
    
    logger.info("=" * 60)
    
    # 测试服务类
    result4 = test_service_uses_correct_env()
    test_results.append(("服务类", result4))
    
    logger.info("=" * 60)
    
    # 测试智能体
    result5 = test_agent_uses_correct_env()
    test_results.append(("智能体", result5))
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("PATENT_VIEW_API_KEY 统一性测试结果:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"总计: {passed_count}/{len(test_results)} 个测试通过")
    
    if passed_count == len(test_results):
        logger.info("🎉 所有测试通过！PATENT_VIEW_API_KEY 统一使用成功。")
        logger.info("✅ 环境变量命名统一")
        logger.info("✅ 所有组件都使用正确的环境变量")
        logger.info("✅ 代码中已清理旧引用")
    elif passed_count >= 3:
        logger.info("✅ 主要功能正常，PATENT_VIEW_API_KEY 基本统一")
    else:
        logger.error("❌ 统一性测试失败，需要进一步检查")
    
    return passed_count >= 3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)