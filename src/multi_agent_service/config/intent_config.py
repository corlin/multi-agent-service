"""Intent recognition and routing configuration."""

from typing import Dict, List, Any
from ..models.enums import IntentType, AgentType


class IntentConfig:
    """意图识别和路由配置类."""
    
    @staticmethod
    def get_intent_patterns() -> Dict[IntentType, Dict[str, Any]]:
        """获取意图识别模式配置.
        
        Returns:
            Dict[IntentType, Dict[str, Any]]: 意图模式配置
        """
        return {
            IntentType.SALES_INQUIRY: {
                "keywords": [
                    "价格", "报价", "多少钱", "费用", "成本",
                    "购买", "订购", "下单", "采购",
                    "产品", "服务", "方案", "套餐",
                    "优惠", "折扣", "促销", "活动",
                    "销售", "业务", "合作", "代理"
                ],
                "patterns": [
                    r".*价格.*",
                    r".*多少钱.*",
                    r".*购买.*",
                    r".*产品.*介绍.*",
                    r".*报价.*"
                ],
                "entities": ["PRODUCT", "PRICE", "SERVICE", "COMPANY"],
                "confidence_boost": 0.1
            },
            
            IntentType.CUSTOMER_SUPPORT: {
                "keywords": [
                    "问题", "故障", "错误", "异常", "不能",
                    "帮助", "支持", "咨询", "解决",
                    "使用", "操作", "功能", "设置",
                    "投诉", "建议", "反馈", "意见"
                ],
                "patterns": [
                    r".*问题.*",
                    r".*故障.*",
                    r".*不能.*",
                    r".*怎么.*",
                    r".*如何.*"
                ],
                "entities": ["PROBLEM", "FEATURE", "CONTACT"],
                "confidence_boost": 0.05
            },
            
            IntentType.TECHNICAL_SERVICE: {
                "keywords": [
                    "维修", "修理", "安装", "调试", "配置",
                    "技术", "工程师", "现场", "上门",
                    "设备", "系统", "软件", "硬件",
                    "部署", "实施", "集成", "测试"
                ],
                "patterns": [
                    r".*维修.*",
                    r".*安装.*",
                    r".*技术.*支持.*",
                    r".*现场.*服务.*",
                    r".*工程师.*"
                ],
                "entities": ["SERVICE", "LOCATION", "DATE", "PROBLEM"],
                "confidence_boost": 0.15
            },
            
            IntentType.MANAGEMENT_DECISION: {
                "keywords": [
                    "决策", "管理", "策略", "规划", "方案",
                    "分析", "报告", "数据", "统计",
                    "预算", "投资", "资源", "配置",
                    "政策", "制度", "流程", "优化"
                ],
                "patterns": [
                    r".*决策.*",
                    r".*管理.*",
                    r".*策略.*",
                    r".*分析.*报告.*",
                    r".*预算.*"
                ],
                "entities": ["COMPANY", "DATE", "PERSON"],
                "confidence_boost": 0.2
            },
            
            IntentType.GENERAL_INQUIRY: {
                "keywords": [
                    "了解", "介绍", "什么是", "关于",
                    "信息", "资料", "详情", "说明",
                    "公司", "企业", "业务", "服务",
                    "联系", "地址", "电话", "邮箱"
                ],
                "patterns": [
                    r".*什么是.*",
                    r".*了解.*",
                    r".*介绍.*",
                    r".*关于.*",
                    r".*联系.*"
                ],
                "entities": ["COMPANY", "CONTACT", "LOCATION"],
                "confidence_boost": 0.0
            },
            
            IntentType.COLLABORATION_REQUIRED: {
                "keywords": [
                    "复杂", "综合", "多个", "各种",
                    "协作", "配合", "联合", "共同",
                    "整体", "全面", "系统", "完整",
                    "跨部门", "多方面", "一体化"
                ],
                "patterns": [
                    r".*复杂.*问题.*",
                    r".*多个.*方面.*",
                    r".*综合.*解决.*",
                    r".*协作.*",
                    r".*跨部门.*"
                ],
                "entities": ["COMPANY", "SERVICE", "PROBLEM"],
                "confidence_boost": 0.25
            }
        }
    
    @staticmethod
    def get_routing_rules() -> Dict[IntentType, Dict[str, Any]]:
        """获取路由规则配置.
        
        Returns:
            Dict[IntentType, Dict[str, Any]]: 路由规则配置
        """
        return {
            IntentType.SALES_INQUIRY: {
                "primary_agents": [AgentType.SALES],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.7,
                "requires_collaboration": False,
                "max_processing_time": 300,  # 5分钟
                "priority_multiplier": 1.0
            },
            
            IntentType.CUSTOMER_SUPPORT: {
                "primary_agents": [AgentType.CUSTOMER_SUPPORT],
                "fallback_agents": [AgentType.FIELD_SERVICE, AgentType.SALES],
                "confidence_threshold": 0.6,
                "requires_collaboration": False,
                "max_processing_time": 600,  # 10分钟
                "priority_multiplier": 1.2
            },
            
            IntentType.TECHNICAL_SERVICE: {
                "primary_agents": [AgentType.FIELD_SERVICE],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.75,
                "requires_collaboration": False,
                "max_processing_time": 900,  # 15分钟
                "priority_multiplier": 1.5
            },
            
            IntentType.MANAGEMENT_DECISION: {
                "primary_agents": [AgentType.MANAGER],
                "fallback_agents": [AgentType.COORDINATOR],
                "confidence_threshold": 0.8,
                "requires_collaboration": True,
                "max_processing_time": 1800,  # 30分钟
                "priority_multiplier": 2.0
            },
            
            IntentType.GENERAL_INQUIRY: {
                "primary_agents": [AgentType.CUSTOMER_SUPPORT],
                "fallback_agents": [AgentType.SALES],
                "confidence_threshold": 0.5,
                "requires_collaboration": False,
                "max_processing_time": 180,  # 3分钟
                "priority_multiplier": 0.8
            },
            
            IntentType.COLLABORATION_REQUIRED: {
                "primary_agents": [AgentType.COORDINATOR],
                "fallback_agents": [AgentType.MANAGER, AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.85,
                "requires_collaboration": True,
                "max_processing_time": 2400,  # 40分钟
                "priority_multiplier": 2.5
            }
        }
    
    @staticmethod
    def get_collaboration_rules() -> Dict[str, Any]:
        """获取协作规则配置.
        
        Returns:
            Dict[str, Any]: 协作规则配置
        """
        return {
            "collaboration_triggers": {
                "low_confidence": 0.6,  # 置信度低于此值触发协作
                "multiple_entities": 4,  # 实体数量超过此值触发协作
                "complex_keywords": [
                    "复杂", "困难", "紧急", "重要", "关键",
                    "多个", "各种", "综合", "全面", "系统"
                ],
                "high_priority": ["high", "urgent"]
            },
            
            "collaboration_strategies": {
                "sequential": {
                    "description": "顺序协作，智能体按顺序处理",
                    "suitable_for": ["management_decision", "technical_service"],
                    "max_agents": 3,
                    "timeout": 1800
                },
                "parallel": {
                    "description": "并行协作，多个智能体同时处理",
                    "suitable_for": ["collaboration_required", "sales_inquiry"],
                    "max_agents": 4,
                    "timeout": 900
                },
                "hierarchical": {
                    "description": "分层协作，协调员统筹管理",
                    "suitable_for": ["collaboration_required", "management_decision"],
                    "max_agents": 5,
                    "timeout": 2400
                }
            },
            
            "agent_compatibility": {
                AgentType.COORDINATOR: [
                    AgentType.SALES, AgentType.MANAGER, 
                    AgentType.FIELD_SERVICE, AgentType.CUSTOMER_SUPPORT
                ],
                AgentType.SALES: [
                    AgentType.CUSTOMER_SUPPORT, AgentType.MANAGER
                ],
                AgentType.MANAGER: [
                    AgentType.SALES, AgentType.FIELD_SERVICE, 
                    AgentType.CUSTOMER_SUPPORT, AgentType.COORDINATOR
                ],
                AgentType.FIELD_SERVICE: [
                    AgentType.CUSTOMER_SUPPORT, AgentType.MANAGER
                ],
                AgentType.CUSTOMER_SUPPORT: [
                    AgentType.SALES, AgentType.FIELD_SERVICE, AgentType.MANAGER
                ]
            }
        }
    
    @staticmethod
    def get_entity_extraction_config() -> Dict[str, Any]:
        """获取实体提取配置.
        
        Returns:
            Dict[str, Any]: 实体提取配置
        """
        return {
            "entity_types": {
                "PRODUCT": {
                    "patterns": [r"产品\w*", r"\w*系统", r"\w*软件", r"\w*设备"],
                    "keywords": ["产品", "系统", "软件", "设备", "方案", "服务"],
                    "confidence_threshold": 0.7
                },
                "PRICE": {
                    "patterns": [r"\d+元", r"\d+万", r"\d+千", r"￥\d+", r"\$\d+"],
                    "keywords": ["价格", "费用", "成本", "报价", "金额"],
                    "confidence_threshold": 0.8
                },
                "SERVICE": {
                    "patterns": [r"\w*服务", r"\w*支持", r"\w*维护"],
                    "keywords": ["服务", "支持", "维护", "咨询", "培训"],
                    "confidence_threshold": 0.7
                },
                "PERSON": {
                    "patterns": [r"\w*经理", r"\w*总监", r"\w*工程师"],
                    "keywords": ["经理", "总监", "工程师", "专员", "顾问"],
                    "confidence_threshold": 0.8
                },
                "COMPANY": {
                    "patterns": [r"\w*公司", r"\w*企业", r"\w*集团"],
                    "keywords": ["公司", "企业", "集团", "机构", "组织"],
                    "confidence_threshold": 0.8
                },
                "DATE": {
                    "patterns": [
                        r"\d{4}年\d{1,2}月\d{1,2}日",
                        r"\d{1,2}月\d{1,2}日",
                        r"今天", r"明天", r"后天", r"下周", r"下月"
                    ],
                    "keywords": ["今天", "明天", "下周", "下月", "尽快"],
                    "confidence_threshold": 0.9
                },
                "LOCATION": {
                    "patterns": [r"\w*市", r"\w*区", r"\w*县", r"\w*省"],
                    "keywords": ["市", "区", "县", "省", "地址", "位置"],
                    "confidence_threshold": 0.8
                },
                "PROBLEM": {
                    "patterns": [r"\w*问题", r"\w*故障", r"\w*错误"],
                    "keywords": ["问题", "故障", "错误", "异常", "bug"],
                    "confidence_threshold": 0.7
                },
                "FEATURE": {
                    "patterns": [r"\w*功能", r"\w*特性", r"\w*模块"],
                    "keywords": ["功能", "特性", "模块", "组件", "接口"],
                    "confidence_threshold": 0.7
                },
                "CONTACT": {
                    "patterns": [
                        r"1[3-9]\d{9}",  # 手机号
                        r"\w+@\w+\.\w+",  # 邮箱
                        r"\d{3,4}-\d{7,8}"  # 电话
                    ],
                    "keywords": ["电话", "手机", "邮箱", "联系", "微信"],
                    "confidence_threshold": 0.9
                }
            },
            
            "extraction_strategies": {
                "regex_based": {
                    "enabled": True,
                    "weight": 0.3
                },
                "keyword_based": {
                    "enabled": True,
                    "weight": 0.2
                },
                "llm_based": {
                    "enabled": True,
                    "weight": 0.5
                }
            },
            
            "post_processing": {
                "normalize_entities": True,
                "merge_similar_entities": True,
                "filter_low_confidence": True,
                "min_confidence": 0.5
            }
        }