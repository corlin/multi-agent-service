"""测试 API 密钥加载."""

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


def test_env_loading():
    """测试环境变量加载."""
    
    logger.info("测试环境变量加载")
    
    # 检查 .env 文件是否存在
    env_file = ".env"
    if os.path.exists(env_file):
        logger.info(f"✅ 找到 .env 文件: {env_file}")
    else:
        logger.warning(f"⚠️ 未找到 .env 文件: {env_file}")
    
    # 尝试加载 python-dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ 成功加载 python-dotenv")
    except ImportError:
        logger.warning("⚠️ 未安装 python-dotenv，尝试手动加载环境变量")
        # 手动加载 .env 文件
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            logger.info("✅ 手动加载 .env 文件完成")
    
    # 检查 API 密钥
    patent_view_key = os.getenv('PATENT_VIEW_API_KEY')
    patentsview_key = os.getenv('PATENTSVIEW_API_KEY')
    
    logger.info(f"PATENT_VIEW_API_KEY: {'✅ 已设置' if patent_view_key else '❌ 未设置'}")
    if patent_view_key:
        logger.info(f"  值: {patent_view_key[:10]}...{patent_view_key[-5:] if len(patent_view_key) > 15 else patent_view_key}")
    
    logger.info(f"PATENTSVIEW_API_KEY: {'✅ 已设置' if patentsview_key else '❌ 未设置'}")
    if patentsview_key:
        logger.info(f"  值: {patentsview_key[:10]}...{patentsview_key[-5:] if len(patentsview_key) > 15 else patentsview_key}")
    
    return patent_view_key or patentsview_key


def test_config_loading():
    """测试配置加载."""
    
    logger.info("测试 PatentsView 配置加载")
    
    try:
        from src.multi_agent_service.patent.config.patentsview_config import PatentsViewAPIConfig
        
        config = PatentsViewAPIConfig.from_env()
        
        logger.info(f"API 基础URL: {config.base_url}")
        logger.info(f"API 密钥: {'✅ 已配置' if config.api_key else '❌ 未配置'}")
        if config.api_key:
            logger.info(f"  密钥长度: {len(config.api_key)} 字符")
            logger.info(f"  密钥预览: {config.api_key[:10]}...{config.api_key[-5:] if len(config.api_key) > 15 else config.api_key}")
        
        logger.info(f"超时设置: {config.timeout}秒")
        logger.info(f"最大重试: {config.max_retries}次")
        logger.info(f"默认页面大小: {config.default_page_size}")
        
        return config.api_key is not None
        
    except Exception as e:
        logger.error(f"❌ 配置加载失败: {str(e)}")
        return False


def test_service_initialization():
    """测试服务初始化."""
    
    logger.info("测试 PatentsView 服务初始化")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        service = PatentsViewService()
        
        logger.info(f"服务 API 密钥: {'✅ 已配置' if service.api_key else '❌ 未配置'}")
        if service.api_key:
            logger.info(f"  密钥长度: {len(service.api_key)} 字符")
            logger.info(f"  密钥预览: {service.api_key[:10]}...{service.api_key[-5:] if len(service.api_key) > 15 else service.api_key}")
        
        logger.info(f"服务基础URL: {service.base_url}")
        
        return service.api_key is not None
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {str(e)}")
        return False


def main():
    """主测试函数."""
    
    logger.info("开始 API 密钥加载测试")
    logger.info("=" * 50)
    
    # 测试环境变量加载
    env_result = test_env_loading()
    
    logger.info("=" * 50)
    
    # 测试配置加载
    config_result = test_config_loading()
    
    logger.info("=" * 50)
    
    # 测试服务初始化
    service_result = test_service_initialization()
    
    logger.info("=" * 50)
    
    # 汇总结果
    logger.info("测试结果汇总:")
    logger.info(f"环境变量加载: {'✅ 通过' if env_result else '❌ 失败'}")
    logger.info(f"配置加载: {'✅ 通过' if config_result else '❌ 失败'}")
    logger.info(f"服务初始化: {'✅ 通过' if service_result else '❌ 失败'}")
    
    all_passed = env_result and config_result and service_result
    
    if all_passed:
        logger.info("🎉 所有测试通过！API 密钥配置正确。")
    else:
        logger.error("❌ 部分测试失败，请检查 API 密钥配置。")
        
        if not env_result:
            logger.error("  - 请确保 .env 文件中包含 PATENT_VIEW_API_KEY")
        if not config_result:
            logger.error("  - 请检查配置类是否正确读取环境变量")
        if not service_result:
            logger.error("  - 请检查服务类是否正确初始化 API 密钥")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)