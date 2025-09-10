"""Configuration management service for multi-agent system."""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from threading import Lock
from datetime import datetime

from .settings import Settings
from .intent_config import IntentConfig
from ..models.config import AgentConfig, ModelConfig, WorkflowConfig
from ..utils.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更监听器."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        
    def on_modified(self, event):
        """文件修改事件处理."""
        if not event.is_directory and event.src_path.endswith(('.json', '.yaml', '.yml', '.env')):
            logger.info(f"Configuration file modified: {event.src_path}")
            self.config_manager._reload_config_file(event.src_path)


class ConfigManager:
    """配置管理器，负责加载、验证和管理所有配置."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器.
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self._config_cache: Dict[str, Any] = {}
        self._config_lock = Lock()
        self._observers: List[Observer] = []
        self._settings: Optional[Settings] = None
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._model_configs: Dict[str, ModelConfig] = {}
        self._workflow_configs: Dict[str, WorkflowConfig] = {}
        self._intent_config: Optional[IntentConfig] = None
        self._last_reload_time = datetime.now()
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化配置
        self._initialize_configs()
    
    def _initialize_configs(self) -> None:
        """初始化所有配置."""
        try:
            # 加载基础设置
            self._settings = Settings()
            
            # 加载意图配置
            self._intent_config = IntentConfig()
            
            # 加载配置文件
            self._load_all_config_files()
            
            # 验证配置
            self._validate_all_configs()
            
            logger.info("Configuration manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize configuration manager: {e}")
            raise ConfigurationError(f"Configuration initialization failed: {e}")
    
    def _load_all_config_files(self) -> None:
        """加载所有配置文件."""
        config_files = {
            "agents.json": self._load_agent_configs,
            "models.json": self._load_model_configs,
            "workflows.json": self._load_workflow_configs,
            "agents.yaml": self._load_agent_configs,
            "models.yaml": self._load_model_configs,
            "workflows.yaml": self._load_workflow_configs,
            # Patent analysis configurations
            "patent_agents.json": self._load_agent_configs,
            "patent_workflows.json": self._load_workflow_configs,
            "patent_agents.yaml": self._load_agent_configs,
            "patent_workflows.yaml": self._load_workflow_configs,
        }
        
        for filename, loader_func in config_files.items():
            config_path = self.config_dir / filename
            if config_path.exists():
                try:
                    loader_func(config_path)
                    logger.info(f"Loaded configuration from {config_path}")
                except Exception as e:
                    logger.warning(f"Failed to load {config_path}: {e}")
    
    def _load_config_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """加载配置文件.
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
            
        Raises:
            ConfigurationError: 配置文件加载失败
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 替换环境变量占位符
                content = self._substitute_env_vars(content)
                
                if file_path.suffix.lower() == '.json':
                    return json.loads(content)
                elif file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(content) or {}
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
                    
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Failed to parse configuration file {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file {file_path}: {e}")
    
    def _substitute_env_vars(self, content: str) -> str:
        """替换配置文件中的环境变量占位符.
        
        Args:
            content: 配置文件内容
            
        Returns:
            str: 替换后的内容
        """
        import re
        from dotenv import load_dotenv
        
        # 确保加载.env文件
        load_dotenv()
        
        def replace_env_var(match):
            env_var = match.group(1)
            env_value = os.getenv(env_var)
            if env_value is None:
                logger.warning(f"Environment variable {env_var} not found, keeping placeholder")
                return match.group(0)  # 保持原占位符
            return env_value
        
        # 匹配 ${VAR_NAME} 格式的占位符
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_env_var, content)
    
    def _load_agent_configs(self, config_path: Path) -> None:
        """加载智能体配置."""
        config_data = self._load_config_file(config_path)
        
        for agent_id, agent_data in config_data.get("agents", {}).items():
            try:
                # 应用默认值
                agent_data = self._apply_agent_defaults(agent_data)
                
                # 创建配置对象
                agent_config = AgentConfig(**agent_data)
                self._agent_configs[agent_id] = agent_config
                
            except ValidationError as e:
                logger.error(f"Invalid agent configuration for {agent_id}: {e}")
                raise ConfigurationError(f"Invalid agent configuration for {agent_id}: {e}")
    
    def _load_model_configs(self, config_path: Path) -> None:
        """加载模型配置."""
        config_data = self._load_config_file(config_path)
        
        for model_id, model_data in config_data.get("models", {}).items():
            try:
                # 应用默认值
                model_data = self._apply_model_defaults(model_data)
                
                # 创建配置对象
                model_config = ModelConfig(**model_data)
                self._model_configs[model_id] = model_config
                
            except ValidationError as e:
                logger.error(f"Invalid model configuration for {model_id}: {e}")
                raise ConfigurationError(f"Invalid model configuration for {model_id}: {e}")
    
    def _load_workflow_configs(self, config_path: Path) -> None:
        """加载工作流配置."""
        config_data = self._load_config_file(config_path)
        
        for workflow_id, workflow_data in config_data.get("workflows", {}).items():
            try:
                # 应用默认值
                workflow_data = self._apply_workflow_defaults(workflow_data)
                
                # 创建配置对象
                workflow_config = WorkflowConfig(**workflow_data)
                self._workflow_configs[workflow_id] = workflow_config
                
            except ValidationError as e:
                logger.error(f"Invalid workflow configuration for {workflow_id}: {e}")
                raise ConfigurationError(f"Invalid workflow configuration for {workflow_id}: {e}")
    
    def _apply_agent_defaults(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """应用智能体配置默认值."""
        defaults = {
            "enabled": True,
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 300,
            "retry_count": 3,
            "capabilities": [],
            "model_config": {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7
            }
        }
        
        # 递归合并默认值
        return self._merge_defaults(agent_data, defaults)
    
    def _apply_model_defaults(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """应用模型配置默认值."""
        defaults = {
            "enabled": True,
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 30,
            "retry_count": 3,
            "rate_limit": 100,
            "priority": 1
        }
        
        return self._merge_defaults(model_data, defaults)
    
    def _apply_workflow_defaults(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """应用工作流配置默认值."""
        defaults = {
            "enabled": True,
            "timeout": 1800,
            "max_agents": 5,
            "retry_count": 2,
            "parallel_execution": False
        }
        
        return self._merge_defaults(workflow_data, defaults)
    
    def _merge_defaults(self, data: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并默认值."""
        result = defaults.copy()
        
        for key, value in data.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_defaults(value, result[key])
            else:
                result[key] = value
        
        return result
    
    def _validate_all_configs(self) -> None:
        """验证所有配置."""
        # 验证智能体配置
        for agent_id, config in self._agent_configs.items():
            self._validate_agent_config(agent_id, config)
        
        # 验证模型配置
        for model_id, config in self._model_configs.items():
            self._validate_model_config(model_id, config)
        
        # 验证工作流配置
        for workflow_id, config in self._workflow_configs.items():
            self._validate_workflow_config(workflow_id, config)
    
    def _validate_agent_config(self, agent_id: str, config: AgentConfig) -> None:
        """验证智能体配置."""
        # 检查必需的字段
        if not config.name:
            raise ConfigurationError(f"Agent {agent_id} missing required field: name")
        
        if not config.agent_type:
            raise ConfigurationError(f"Agent {agent_id} missing required field: agent_type")
        
        # 检查模型配置
        if config.model_config and config.model_config.model_name:
            model_id = config.model_config.model_name
            if model_id not in self._model_configs:
                logger.warning(f"Agent {agent_id} references unknown model: {model_id}")
    
    def _validate_model_config(self, model_id: str, config: ModelConfig) -> None:
        """验证模型配置."""
        # 检查必需的字段
        if not config.provider:
            raise ConfigurationError(f"Model {model_id} missing required field: provider")
        
        if not config.model_name:
            raise ConfigurationError(f"Model {model_id} missing required field: model_name")
        
        # 检查API密钥
        if config.provider == "openai" and not self._settings.openai_api_key:
            logger.warning(f"Model {model_id} requires OpenAI API key")
        elif config.provider == "qwen" and not self._settings.qwen_api_key:
            logger.warning(f"Model {model_id} requires Qwen API key")
        elif config.provider == "deepseek" and not self._settings.deepseek_api_key:
            logger.warning(f"Model {model_id} requires DeepSeek API key")
        elif config.provider == "glm" and not self._settings.glm_api_key:
            logger.warning(f"Model {model_id} requires GLM API key")
    
    def _validate_workflow_config(self, workflow_id: str, config: WorkflowConfig) -> None:
        """验证工作流配置."""
        # 检查必需的字段
        if not config.name:
            raise ConfigurationError(f"Workflow {workflow_id} missing required field: name")
        
        if not config.workflow_type:
            raise ConfigurationError(f"Workflow {workflow_id} missing required field: workflow_type")
    
    def get_settings(self) -> Settings:
        """获取应用设置."""
        if self._settings is None:
            self._settings = Settings()
        return self._settings
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取智能体配置."""
        return self._agent_configs.get(agent_id)
    
    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """获取所有智能体配置."""
        return self._agent_configs.copy()
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """获取模型配置."""
        return self._model_configs.get(model_id)
    
    def get_all_model_configs(self) -> Dict[str, ModelConfig]:
        """获取所有模型配置."""
        return self._model_configs.copy()
    
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置."""
        return self._workflow_configs.get(workflow_id)
    
    def get_all_workflow_configs(self) -> Dict[str, WorkflowConfig]:
        """获取所有工作流配置."""
        return self._workflow_configs.copy()
    
    def get_intent_config(self) -> IntentConfig:
        """获取意图配置."""
        if self._intent_config is None:
            self._intent_config = IntentConfig()
        return self._intent_config
    
    def update_agent_config(self, agent_id: str, config: AgentConfig) -> None:
        """更新智能体配置."""
        with self._config_lock:
            # 验证配置
            self._validate_agent_config(agent_id, config)
            
            # 更新配置
            self._agent_configs[agent_id] = config
            
            # 保存到文件
            self._save_agent_configs()
            
            logger.info(f"Updated agent configuration: {agent_id}")
    
    def update_model_config(self, model_id: str, config: ModelConfig) -> None:
        """更新模型配置."""
        with self._config_lock:
            # 验证配置
            self._validate_model_config(model_id, config)
            
            # 更新配置
            self._model_configs[model_id] = config
            
            # 保存到文件
            self._save_model_configs()
            
            logger.info(f"Updated model configuration: {model_id}")
    
    def update_workflow_config(self, workflow_id: str, config: WorkflowConfig) -> None:
        """更新工作流配置."""
        with self._config_lock:
            # 验证配置
            self._validate_workflow_config(workflow_id, config)
            
            # 更新配置
            self._workflow_configs[workflow_id] = config
            
            # 保存到文件
            self._save_workflow_configs()
            
            logger.info(f"Updated workflow configuration: {workflow_id}")
    
    def _save_agent_configs(self) -> None:
        """保存智能体配置到文件."""
        config_data = {
            "agents": {
                agent_id: config.model_dump()
                for agent_id, config in self._agent_configs.items()
            }
        }
        
        config_path = self.config_dir / "agents.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def _save_model_configs(self) -> None:
        """保存模型配置到文件."""
        config_data = {
            "models": {
                model_id: config.model_dump()
                for model_id, config in self._model_configs.items()
            }
        }
        
        config_path = self.config_dir / "models.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def _save_workflow_configs(self) -> None:
        """保存工作流配置到文件."""
        config_data = {
            "workflows": {
                workflow_id: config.model_dump()
                for workflow_id, config in self._workflow_configs.items()
            }
        }
        
        config_path = self.config_dir / "workflows.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def reload_config(self, config_type: Optional[str] = None) -> None:
        """重新加载配置.
        
        Args:
            config_type: 配置类型 ('agents', 'models', 'workflows', None表示全部)
        """
        with self._config_lock:
            try:
                if config_type is None or config_type == "settings":
                    self._settings = Settings()
                
                if config_type is None or config_type == "agents":
                    self._agent_configs.clear()
                    for filename in ["agents.json", "agents.yaml", "patent_agents.json", "patent_agents.yaml"]:
                        config_path = self.config_dir / filename
                        if config_path.exists():
                            self._load_agent_configs(config_path)
                
                if config_type is None or config_type == "models":
                    self._model_configs.clear()
                    for filename in ["models.json", "models.yaml"]:
                        config_path = self.config_dir / filename
                        if config_path.exists():
                            self._load_model_configs(config_path)
                
                if config_type is None or config_type == "workflows":
                    self._workflow_configs.clear()
                    for filename in ["workflows.json", "workflows.yaml", "patent_workflows.json", "patent_workflows.yaml"]:
                        config_path = self.config_dir / filename
                        if config_path.exists():
                            self._load_workflow_configs(config_path)
                
                # 重新验证配置
                self._validate_all_configs()
                
                self._last_reload_time = datetime.now()
                logger.info(f"Configuration reloaded: {config_type or 'all'}")
                
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
                raise ConfigurationError(f"Configuration reload failed: {e}")
    
    def _reload_config_file(self, file_path: str) -> None:
        """重新加载指定的配置文件."""
        file_path = Path(file_path)
        filename = file_path.name
        
        try:
            if filename.startswith("agents.") or filename.startswith("patent_agents."):
                self._load_agent_configs(file_path)
            elif filename.startswith("models."):
                self._load_model_configs(file_path)
            elif filename.startswith("workflows.") or filename.startswith("patent_workflows."):
                self._load_workflow_configs(file_path)
            elif filename == ".env":
                self._settings = Settings()
            
            self._validate_all_configs()
            self._last_reload_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to reload config file {file_path}: {e}")
    
    def start_file_watching(self) -> None:
        """启动配置文件监控."""
        if self._observers:
            return  # 已经启动
        
        try:
            # 监控配置目录
            observer = Observer()
            event_handler = ConfigFileHandler(self)
            observer.schedule(event_handler, str(self.config_dir), recursive=True)
            observer.start()
            self._observers.append(observer)
            
            # 监控.env文件
            env_path = Path(".env")
            if env_path.exists():
                observer = Observer()
                observer.schedule(event_handler, str(env_path.parent), recursive=False)
                observer.start()
                self._observers.append(observer)
            
            logger.info("Configuration file watching started")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
    
    def stop_file_watching(self) -> None:
        """停止配置文件监控."""
        for observer in self._observers:
            observer.stop()
            observer.join()
        
        self._observers.clear()
        logger.info("Configuration file watching stopped")
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态信息."""
        return {
            "last_reload_time": self._last_reload_time.isoformat(),
            "agent_configs_count": len(self._agent_configs),
            "model_configs_count": len(self._model_configs),
            "workflow_configs_count": len(self._workflow_configs),
            "file_watching_active": len(self._observers) > 0,
            "config_directory": str(self.config_dir),
            "settings_loaded": self._settings is not None
        }
    
    def export_config(self, output_path: str, config_type: Optional[str] = None) -> None:
        """导出配置到文件.
        
        Args:
            output_path: 输出文件路径
            config_type: 配置类型 ('agents', 'models', 'workflows', None表示全部)
        """
        output_path = Path(output_path)
        
        config_data = {}
        
        if config_type is None or config_type == "agents":
            config_data["agents"] = {
                agent_id: config.model_dump()
                for agent_id, config in self._agent_configs.items()
            }
        
        if config_type is None or config_type == "models":
            config_data["models"] = {
                model_id: config.model_dump()
                for model_id, config in self._model_configs.items()
            }
        
        if config_type is None or config_type == "workflows":
            config_data["workflows"] = {
                workflow_id: config.model_dump()
                for workflow_id, config in self._workflow_configs.items()
            }
        
        if config_type is None or config_type == "settings":
            config_data["settings"] = self._settings.model_dump() if self._settings else {}
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_path.suffix.lower() == '.json':
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            elif output_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ConfigurationError(f"Unsupported export format: {output_path.suffix}")
        
        logger.info(f"Configuration exported to {output_path}")
    
    def __enter__(self):
        """上下文管理器入口."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口."""
        self.stop_file_watching()


# 全局配置管理器实例
config_manager = ConfigManager()