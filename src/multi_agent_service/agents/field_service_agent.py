"""Field service agent implementation."""

import re
from typing import Dict, List, Any
from datetime import datetime

from .base import BaseAgent
from ..models.base import UserRequest, AgentResponse, Action
from ..models.config import AgentConfig
from ..models.enums import AgentType
from ..services.model_client import BaseModelClient


class FieldServiceAgent(BaseAgent):
    """现场服务人员智能体，专门处理现场技术服务和故障处理."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化现场服务人员智能体."""
        super().__init__(config, model_client)
        
        # 现场服务相关的关键词
        self.service_keywords = [
            "现场", "上门", "维修", "安装", "调试", "检修", "巡检", "保养",
            "故障", "报修", "抢修", "应急", "紧急", "设备", "机器", "系统",
            "技术", "工程师", "服务", "支持", "处理", "解决", "修复", "更换",
            "field", "onsite", "repair", "install", "maintenance", "service",
            "equipment", "system", "technical", "engineer", "fix", "replace"
        ]
        
        # 服务类型分类
        self.service_types = {
            "设备维修": ["维修", "修理", "故障", "损坏", "异常", "报修"],
            "设备安装": ["安装", "部署", "配置", "调试", "上线", "投产"],
            "设备保养": ["保养", "维护", "巡检", "检查", "清洁", "润滑"],
            "应急抢修": ["紧急", "应急", "抢修", "故障", "停机", "中断"],
            "技术升级": ["升级", "改造", "更新", "优化", "扩容", "迁移"],
            "培训指导": ["培训", "指导", "教学", "演示", "操作", "使用"]
        }
        
        # 紧急程度分级
        self.urgency_levels = {
            "紧急": ["紧急", "立即", "马上", "停机", "中断", "无法使用"],
            "高": ["尽快", "优先", "重要", "影响业务", "多人反馈"],
            "中": ["正常", "计划", "预约", "方便时", "工作时间"],
            "低": ["不急", "有时间", "顺便", "例行", "定期"]
        }
        
        # 常见设备类型和故障
        self.equipment_types = {
            "服务器": {
                "common_issues": ["无法启动", "性能缓慢", "硬盘故障", "内存错误", "网络中断"],
                "tools_needed": ["诊断工具", "备用硬件", "网络测试仪"]
            },
            "网络设备": {
                "common_issues": ["连接中断", "速度慢", "配置错误", "端口故障", "信号弱"],
                "tools_needed": ["网络测试仪", "光功率计", "配置工具"]
            },
            "打印设备": {
                "common_issues": ["卡纸", "打印质量差", "无法连接", "耗材用完", "驱动问题"],
                "tools_needed": ["清洁工具", "备用耗材", "驱动程序"]
            },
            "监控设备": {
                "common_issues": ["画面模糊", "无信号", "存储满", "镜头脏污", "网络断开"],
                "tools_needed": ["清洁工具", "测试设备", "备用存储"]
            }
        }
        
        # 标准服务流程
        self.service_procedures = {
            "故障诊断": [
                "1. 了解故障现象和发生时间",
                "2. 检查设备外观和连接",
                "3. 查看错误日志和状态指示",
                "4. 使用诊断工具进行检测",
                "5. 确定故障原因和影响范围"
            ],
            "维修处理": [
                "1. 制定维修方案和安全措施",
                "2. 准备必要的工具和备件",
                "3. 按照标准流程进行维修",
                "4. 测试修复效果和功能",
                "5. 记录维修过程和结果"
            ],
            "设备安装": [
                "1. 确认安装环境和条件",
                "2. 检查设备和配件完整性",
                "3. 按照技术规范进行安装",
                "4. 进行功能测试和调试",
                "5. 提供操作培训和文档"
            ]
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理现场服务相关请求."""
        content = request.content.lower()
        
        # 检查现场服务关键词
        keyword_matches = sum(1 for keyword in self.service_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.15, 0.6)
        
        # 检查现场服务意图模式
        service_patterns = [
            r"(现场|上门).*?(服务|维修|安装)",
            r"(设备|机器|系统).*?(故障|维修|保养)",
            r"(需要|请求).*?(技术|工程师|服务)",
            r"(紧急|应急).*?(抢修|维修|处理)",
            r"(安装|调试|配置).*?(设备|系统)",
            # English patterns
            r"(field|onsite).*?(service|repair|install)",
            r"(equipment|system).*?(failure|repair|maintenance)",
            r"(need|request).*?(technical|engineer|service)",
            r"(urgent|emergency).*?(repair|fix|service)"
        ]
        
        pattern_score = 0
        for pattern in service_patterns:
            if re.search(pattern, content):
                pattern_score += 0.2
        
        # 基础现场服务意图检查
        base_service_score = 0
        chinese_service_words = ["现场", "维修", "安装", "设备", "故障", "技术", "服务", "工程师"]
        english_service_words = ["field", "repair", "install", "equipment", "technical", "service", "engineer"]
        
        if any(word in content for word in chinese_service_words + english_service_words):
            base_service_score = 0.4
        
        total_score = min(keyword_score + pattern_score + base_service_score, 1.0)
        
        # 如果明确提到销售或管理问题，降低置信度
        other_domain_keywords = ["价格", "购买", "战略", "管理", "决策", "客服咨询"]
        if any(keyword in content for keyword in other_domain_keywords):
            total_score *= 0.6
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取现场服务人员的能力列表."""
        return [
            "故障诊断",
            "设备维修",
            "设备安装",
            "系统调试",
            "预防保养",
            "应急抢修",
            "技术培训",
            "现场支持"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间."""
        content = request.content.lower()
        
        # 简单咨询：5-10秒
        if any(word in content for word in ["咨询", "了解", "询问"]):
            return 8
        
        # 故障诊断：15-25秒
        if any(word in content for word in ["故障", "问题", "异常"]):
            return 20
        
        # 现场服务安排：20-30秒
        if any(word in content for word in ["现场", "上门", "安排"]):
            return 25
        
        # 紧急情况：10-15秒（快速响应）
        if any(word in content for word in ["紧急", "应急", "立即"]):
            return 12
        
        # 默认处理时间
        return 15
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理现场服务相关的具体请求."""
        content = request.content
        
        # 分析服务类型和紧急程度
        service_type = self._identify_service_type(content)
        urgency_level = self._assess_urgency(content)
        equipment_type = self._identify_equipment_type(content)
        
        # 根据服务类型生成响应
        if service_type == "设备维修":
            response_content = await self._handle_equipment_repair(content, equipment_type)
        elif service_type == "设备安装":
            response_content = await self._handle_equipment_installation(content)
        elif service_type == "设备保养":
            response_content = await self._handle_equipment_maintenance(content)
        elif service_type == "应急抢修":
            response_content = await self._handle_emergency_repair(content)
        elif service_type == "技术升级":
            response_content = await self._handle_technical_upgrade(content)
        elif service_type == "培训指导":
            response_content = await self._handle_training_guidance(content)
        else:
            # 使用通用现场服务响应
            response_content = await self._generate_general_service_response(content)
        
        # 生成后续动作建议
        next_actions = self._generate_next_actions(service_type, urgency_level, content)
        
        # 判断是否需要协作
        needs_collaboration = self._needs_collaboration(content, service_type, urgency_level)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content=response_content,
            confidence=0.9,
            next_actions=next_actions,
            collaboration_needed=needs_collaboration,
            metadata={
                "service_type": service_type,
                "urgency_level": urgency_level,
                "equipment_type": equipment_type,
                "needs_collaboration": needs_collaboration,
                "processed_at": datetime.now().isoformat()
            }
        )
    
    def _identify_service_type(self, content: str) -> str:
        """识别服务类型."""
        content_lower = content.lower()
        
        for service_type, keywords in self.service_types.items():
            if any(keyword in content_lower for keyword in keywords):
                return service_type
        
        return "一般服务"
    
    def _assess_urgency(self, content: str) -> str:
        """评估紧急程度."""
        content_lower = content.lower()
        
        for urgency, keywords in self.urgency_levels.items():
            if any(keyword in content_lower for keyword in keywords):
                return urgency
        
        return "中"
    
    def _identify_equipment_type(self, content: str) -> str:
        """识别设备类型."""
        content_lower = content.lower()
        
        for equipment, _ in self.equipment_types.items():
            if equipment in content_lower:
                return equipment
        
        # 检查设备相关关键词
        if any(word in content_lower for word in ["服务器", "主机", "server"]):
            return "服务器"
        elif any(word in content_lower for word in ["网络", "交换机", "路由器", "network"]):
            return "网络设备"
        elif any(word in content_lower for word in ["打印机", "printer"]):
            return "打印设备"
        elif any(word in content_lower for word in ["监控", "摄像头", "camera"]):
            return "监控设备"
        
        return "通用设备"
    
    async def _handle_equipment_repair(self, content: str, equipment_type: str) -> str:
        """处理设备维修请求."""
        response = "我来协助您处理设备维修问题。\n\n"
        response += "**故障诊断流程：**\n"
        
        if equipment_type in self.equipment_types:
            equipment_info = self.equipment_types[equipment_type]
            response += f"针对{equipment_type}，常见故障包括：\n"
            for issue in equipment_info["common_issues"]:
                response += f"• {issue}\n"
            response += f"\n需要准备的工具：{', '.join(equipment_info['tools_needed'])}\n\n"
        
        response += "**维修处理步骤：**\n"
        for step in self.service_procedures["故障诊断"]:
            response += f"{step}\n"
        
        response += "\n**安全提醒：**\n"
        response += "• 维修前请确保设备断电\n"
        response += "• 佩戴防静电手套\n"
        response += "• 记录维修过程和更换部件\n\n"
        
        response += "我会安排技术工程师尽快到现场处理，请提供具体的故障现象和联系方式。"
        
        return response
    
    async def _handle_equipment_installation(self, content: str) -> str:
        """处理设备安装请求."""
        response = "设备安装服务流程如下：\n\n"
        response += "**安装前准备：**\n"
        response += "1. 确认安装环境（电源、网络、空间）\n"
        response += "2. 检查设备清单和配件完整性\n"
        response += "3. 准备必要的安装工具\n"
        response += "4. 制定安装计划和时间安排\n\n"
        
        response += "**标准安装流程：**\n"
        for step in self.service_procedures["设备安装"]:
            response += f"{step}\n"
        
        response += "\n**安装后服务：**\n"
        response += "• 设备功能测试和性能验证\n"
        response += "• 用户操作培训\n"
        response += "• 提供技术文档和保修信息\n"
        response += "• 建立维护保养计划\n\n"
        
        response += "请提供设备型号、安装地址和预期安装时间，我会安排专业工程师上门服务。"
        
        return response
    
    async def _handle_equipment_maintenance(self, content: str) -> str:
        """处理设备保养请求."""
        response = "设备预防性保养是确保设备稳定运行的重要措施：\n\n"
        response += "**保养服务内容：**\n"
        response += "1. **外观检查** - 检查设备外观和连接状态\n"
        response += "2. **清洁维护** - 清洁设备内外部灰尘和污垢\n"
        response += "3. **功能测试** - 测试各项功能是否正常\n"
        response += "4. **参数调整** - 优化设备运行参数\n"
        response += "5. **部件更换** - 更换易损耗材和老化部件\n\n"
        
        response += "**保养周期建议：**\n"
        response += "• 日常保养：每周一次\n"
        response += "• 定期保养：每月一次\n"
        response += "• 深度保养：每季度一次\n"
        response += "• 年度大保：每年一次\n\n"
        
        response += "**保养记录：**\n"
        response += "我们会建立设备保养档案，记录每次保养的详细情况，为您提供设备健康报告。\n\n"
        
        response += "请告诉我设备类型和数量，我会制定个性化的保养计划。"
        
        return response
    
    async def _handle_emergency_repair(self, content: str) -> str:
        """处理应急抢修请求."""
        response = "🚨 **应急抢修服务** 🚨\n\n"
        response += "我已收到您的紧急维修请求，将立即启动应急响应流程：\n\n"
        response += "**应急响应时间：**\n"
        response += "• 市区内：30分钟内到达\n"
        response += "• 郊区：60分钟内到达\n"
        response += "• 远程支持：立即提供\n\n"
        
        response += "**应急处理步骤：**\n"
        response += "1. **快速评估** - 评估故障影响和紧急程度\n"
        response += "2. **临时措施** - 采取临时措施减少损失\n"
        response += "3. **紧急修复** - 优先恢复关键功能\n"
        response += "4. **后续处理** - 安排彻底修复方案\n\n"
        
        response += "**需要您提供的信息：**\n"
        response += "• 具体故障现象和错误信息\n"
        response += "• 设备型号和安装位置\n"
        response += "• 联系人和联系方式\n"
        response += "• 现场环境和安全要求\n\n"
        
        response += "⚡ 我已通知最近的技术工程师，请保持电话畅通！"
        
        return response
    
    async def _handle_technical_upgrade(self, content: str) -> str:
        """处理技术升级请求."""
        response = "技术升级服务可以提升设备性能和功能：\n\n"
        response += "**升级评估：**\n"
        response += "1. **现状分析** - 评估当前设备状态和性能\n"
        response += "2. **需求确认** - 明确升级目标和期望\n"
        response += "3. **方案设计** - 制定升级方案和实施计划\n"
        response += "4. **风险评估** - 评估升级风险和应对措施\n\n"
        
        response += "**升级类型：**\n"
        response += "• **硬件升级** - 更换或增加硬件组件\n"
        response += "• **软件升级** - 更新系统和应用软件\n"
        response += "• **功能扩展** - 增加新功能和模块\n"
        response += "• **性能优化** - 优化配置和参数\n\n"
        
        response += "**升级保障：**\n"
        response += "• 数据备份和恢复\n"
        response += "• 兼容性测试\n"
        response += "• 回退方案准备\n"
        response += "• 用户培训支持\n\n"
        
        response += "请提供设备详细信息和升级需求，我会为您制定专业的升级方案。"
        
        return response
    
    async def _handle_training_guidance(self, content: str) -> str:
        """处理培训指导请求."""
        response = "技术培训和操作指导服务：\n\n"
        response += "**培训内容：**\n"
        response += "1. **基础操作** - 设备基本操作和功能介绍\n"
        response += "2. **日常维护** - 日常保养和简单故障处理\n"
        response += "3. **安全规范** - 操作安全和注意事项\n"
        response += "4. **故障排除** - 常见问题的诊断和处理\n"
        response += "5. **最佳实践** - 高效使用技巧和经验分享\n\n"
        
        response += "**培训方式：**\n"
        response += "• **现场培训** - 工程师上门实操培训\n"
        response += "• **远程指导** - 视频通话远程指导\n"
        response += "• **文档资料** - 提供详细操作手册\n"
        response += "• **视频教程** - 录制操作演示视频\n\n"
        
        response += "**培训效果：**\n"
        response += "• 提高操作效率和准确性\n"
        response += "• 减少操作错误和故障\n"
        response += "• 延长设备使用寿命\n"
        response += "• 降低维护成本\n\n"
        
        response += "请告诉我需要培训的设备类型和人员数量，我会安排专业培训师为您服务。"
        
        return response
    
    async def _generate_general_service_response(self, content: str) -> str:
        """生成通用现场服务响应."""
        response = "感谢您联系现场技术服务！\n\n"
        response += "我是专业的现场服务工程师，可以为您提供：\n\n"
        response += "**服务范围：**\n"
        response += "• 设备故障诊断和维修\n"
        response += "• 设备安装和调试\n"
        response += "• 预防性维护保养\n"
        response += "• 应急抢修服务\n"
        response += "• 技术升级和改造\n"
        response += "• 操作培训和指导\n\n"
        
        response += "**服务承诺：**\n"
        response += "• 快速响应，及时到达\n"
        response += "• 专业技术，质量保证\n"
        response += "• 标准流程，规范操作\n"
        response += "• 详细记录，跟踪服务\n\n"
        
        response += "请详细描述您的具体需求，我会为您提供最适合的技术服务方案。"
        
        return response
    
    def _generate_next_actions(self, service_type: str, urgency_level: str, content: str) -> List[Action]:
        """生成后续动作建议."""
        actions = []
        
        if service_type == "应急抢修":
            actions.extend([
                Action(
                    action_type="dispatch_engineer",
                    parameters={"priority": "urgent", "eta": "30_minutes"},
                    description="紧急派遣工程师"
                ),
                Action(
                    action_type="prepare_tools",
                    parameters={"type": "emergency_kit"},
                    description="准备应急工具包"
                )
            ])
        elif service_type == "设备安装":
            actions.extend([
                Action(
                    action_type="site_survey",
                    parameters={"type": "installation_assessment"},
                    description="现场环境评估"
                ),
                Action(
                    action_type="schedule_installation",
                    parameters={"lead_time": "3_days"},
                    description="安排安装时间"
                )
            ])
        elif service_type == "设备维修":
            actions.extend([
                Action(
                    action_type="diagnostic_check",
                    parameters={"method": "remote_first"},
                    description="远程诊断检查"
                ),
                Action(
                    action_type="prepare_parts",
                    parameters={"based_on": "diagnosis"},
                    description="准备维修配件"
                )
            ])
        
        # 根据紧急程度添加动作
        if urgency_level == "紧急":
            actions.append(
                Action(
                    action_type="immediate_response",
                    parameters={"response_time": "15_minutes"},
                    description="立即响应处理"
                )
            )
        
        # 通用后续动作
        actions.append(
            Action(
                action_type="service_follow_up",
                parameters={"schedule": "24_hours"},
                description="24小时内服务跟进"
            )
        )
        
        return actions
    
    def _needs_collaboration(self, content: str, service_type: str, urgency_level: str) -> bool:
        """判断是否需要与其他智能体协作."""
        content_lower = content.lower()
        
        # 涉及采购需要销售协作
        if any(word in content_lower for word in ["采购", "购买", "报价", "合同"]):
            return True
        
        # 涉及客户投诉需要客服协作
        if any(word in content_lower for word in ["投诉", "不满", "赔偿", "责任"]):
            return True
        
        # 重大技术决策需要管理层协作
        if any(word in content_lower for word in ["重大", "批准", "决策", "预算"]):
            return True
        
        # 紧急情况需要多方协调
        if urgency_level == "紧急" and service_type == "应急抢修":
            return True
        
        return False
    
    async def _validate_config(self) -> bool:
        """验证现场服务智能体配置."""
        if self.agent_type != AgentType.FIELD_SERVICE:
            self.logger.error(f"Invalid agent type for FieldServiceAgent: {self.agent_type}")
            return False
        
        required_capabilities = ["field_service", "technical_support", "equipment_maintenance"]
        if not any(cap in self.config.capabilities for cap in required_capabilities):
            self.logger.warning("FieldServiceAgent missing recommended capabilities")
        
        return True
    
    async def _initialize_specific(self) -> bool:
        """现场服务智能体特定的初始化."""
        self.logger.info("Initializing field service specific components...")
        
        # 初始化服务流程和设备信息
        self._load_service_data()
        
        self.logger.info("Field service agent initialization completed")
        return True
    
    def _load_service_data(self):
        """加载现场服务相关数据."""
        self.logger.info(f"Loaded {len(self.equipment_types)} equipment types")
        self.logger.info(f"Loaded {len(self.service_procedures)} service procedures")
    
    async def _health_check_specific(self) -> bool:
        """现场服务智能体特定的健康检查."""
        try:
            test_content = "设备故障需要现场维修"
            confidence = await self.can_handle_request(
                UserRequest(content=test_content)
            )
            if confidence < 0.3:
                self.logger.error("Field service capability test failed")
                return False
        except Exception as e:
            self.logger.error(f"Field service health check failed: {str(e)}")
            return False
        
        return True